"""
Reference:
* https://github.com/facebookincubator/Bowler
* https://github.com/lensvol/astboom
"""

from typing import overload

import libcst as cst
from typing_extensions import Self


class FluentCstNode:
    def to_code(self) -> str:
        cst_node = self.to_cst()
        if isinstance(cst_node, cst.List):
            # TODO(povilas): see if I can remove Expr?
            cst_node = cst.SimpleStatementLine(body=[cst.Expr(value=cst_node)])

        return cst.Module(body=[cst_node]).code

    # TODO(povilas): abstract method
    def to_cst(self) -> cst.SimpleStatementLine | cst.BaseCompoundStatement | cst.List:
        raise NotImplementedError


class RawNode(FluentCstNode):
    def __init__(self, node: cst.BaseExpression) -> None:
        self._node = node

    def to_cst(self) -> cst.BaseExpression:
        return self._node


class String(FluentCstNode):
    """SimpleString for now only."""

    def __init__(self, value: str) -> None:
        self._value = value.replace('"', '\\"')

    def to_cst(self) -> cst.SimpleString:
        return cst.SimpleString(value=f'"{self._value}"')


class Boolean(FluentCstNode):
    def __init__(self, value: bool) -> None:
        self._value = value

    def to_cst(self) -> cst.Expr:
        return cst.Expr(value=cst.Name(value=str(self._value)))


class Integer(FluentCstNode):
    def __init__(self, value: int) -> None:
        self._value = value

    def to_cst(self) -> cst.Integer:
        return cst.Integer(value=str(self._value))


class Name(FluentCstNode):
    """Arbitrary name: could be a variable, class, function, etc."""

    def __init__(self, value: str) -> None:
        self._value = value

    def to_cst(self) -> cst.Name:
        return cst.Name(value=self._value)


class Attribute(FluentCstNode):
    """
    ```py
    fluentcst.Attribute("data.model.field")
    ```
    """

    def __init__(self, path: str) -> None:
        assert "." in path, "Attribute path must contain at least one dot."
        self._path = path
        self._bitor: dict | None = None
        # Only dict supported for now.

    def to_cst(self) -> cst.Attribute | cst.BinaryOperation:
        parts = self._path.split(".")
        last_part = parts.pop()
        attr = cst.Attribute(
            value=self._name_or_attr(parts),
            attr=cst.Name(value=last_part),
        )

        if self._bitor:
            return cst.BinaryOperation(
                left=attr,
                operator=cst.BitOr(),
                right=Dict.from_dict(self._bitor).to_cst(),
            )

        return attr

    def bitor(self, other: dict) -> Self:
        """Bitwise or with another value.
        ```py
        Attribute("resp.data").bitor({"error": ""})
        ```
        """
        self._bitor = other
        return self

    @staticmethod
    def _name_or_attr(parts: list[str]) -> cst.Name | cst.Attribute | cst.Subscript:
        attr = parts.pop()
        if len(parts) == 0:
            return cst.Name(value=attr)

        if attr.endswith("]"):
            path, index = attr.split("[")
            index = index[:-1]
            if index.isalnum():
                index = int(index)
            return _subscript(
                cst.Attribute(
                    value=Attribute._name_or_attr(parts), attr=cst.Name(value=path)
                ),
                _value(index).to_cst(),
            )

        return cst.Attribute(
            value=Attribute._name_or_attr(parts),
            attr=cst.Name(value=attr),
        )

    def __repr__(self) -> str:
        or_part = f" | {self._bitor}" if self._bitor else ""
        return f"Attribute('{self._path}'{or_part})"


class List(FluentCstNode):
    def __init__(self, elements: list["str | bool | Call | RawNode"]) -> None:
        self._elements = elements

    def to_cst(self) -> cst.List:
        elems = [cst.Element(value=_value(v).to_cst()) for v in self._elements]
        return cst.List(elements=elems)


class Dict(FluentCstNode):
    @classmethod
    def from_dict(cls, d: dict) -> Self:
        dict_node = cls()
        for k, v in d.items():
            dict_node.element(k, v)
        return dict_node

    def __init__(self) -> None:
        self._elements: list[tuple[str, str | Attribute]] = []

    def element(self, key: str, value: str | Attribute) -> "Dict":
        self._elements.append((key, value))
        return self

    def to_cst(self) -> cst.Dict:
        dict_elems = [
            cst.DictElement(key=String(k).to_cst(), value=self._recurse(v))
            for k, v in self._elements
        ]
        return cst.Dict(elements=dict_elems)

    @staticmethod
    def _recurse(
        v: str | Attribute | dict | int,
    ) -> (
        cst.SimpleString | cst.Attribute | cst.BinaryOperation | cst.Dict | cst.Integer
    ):
        if isinstance(v, dict):
            return Dict.from_dict(v).to_cst()
        return _value(v).to_cst()


class Annotation(FluentCstNode):
    def __init__(self, type_name: str | list[str]) -> None:
        """
        Args:
            type_name: 'Type' or 'list[Type]'.
        """
        # For a union of types
        self._types = [type_name]

    def or_(self, type_name: str) -> Self:
        self._types.append(type_name)
        return self

    def to_cst(self) -> cst.Annotation:
        return cst.Annotation(self._bit_or(self._types))

    @staticmethod
    def _bit_or(
        args: list[str | list[str]],
    ) -> cst.BinaryOperation | cst.Name | cst.Subscript:
        if len(args) == 1:
            return Annotation._type_name_or_list(args[0])
        else:
            return cst.BinaryOperation(
                left=Annotation._type_name_or_list(args[0]),
                operator=cst.BitOr(),
                right=Annotation._bit_or(args[1:]),
            )

    @staticmethod
    def _type_name_or_list(type_: str | list[str]) -> cst.Name | cst.Subscript:
        if isinstance(type_, list):
            if len(type_) > 0:
                return _subscript(cst.Name(value="list"), cst.Name(value=type_[0]))
            else:
                return cst.Name(value="list")
        return cst.Name(value=type_)


class Call(FluentCstNode):
    def __init__(
        self,
        name__: str,
        *args: str | bool | int | Name | Attribute,
        **kwargs: str | bool | int | dict,
    ) -> None:
        self._name = name__
        self._args = args
        self._kwargs = kwargs

    def to_cst(self) -> cst.Call:
        call_args = [cst.Arg(value=_value(a).to_cst()) for a in self._args] + [
            cst.Arg(value=_value(v).to_cst(), keyword=cst.Name(value=k))
            for k, v in self._kwargs.items()
        ]
        return cst.Call(func=_name_or_attr(self._name), args=call_args)


class ClassDef(FluentCstNode):
    def __init__(self, name: str) -> None:
        self._name = name
        self._fields = []
        self._bases = []

    def base(self, class_name: str) -> Self:
        self._bases.append(class_name)
        return self

    def field(
        self,
        name: str,
        value: str
        | Call
        | dict
        | list[str | Call]
        | list[RawNode]
        | Dict
        | Attribute
        | RawNode
        | None = None,
        type: str | list[str] | None = None,
    ) -> Self:
        if type is not None:
            assign = cst.AnnAssign(
                target=cst.Name(value=name), annotation=Annotation(type).to_cst()
            )
        else:
            assert value is not None, "None is not yet supported"
            value_node = _value(value)
            assign = cst.Assign(
                targets=[cst.AssignTarget(target=cst.Name(value=name))],
                value=value_node.to_cst(),
            )
        field_node = cst.SimpleStatementLine(body=[assign])
        self._fields.append(field_node)

        return self

    def to_cst(self) -> cst.ClassDef:
        bases = [cst.Arg(value=cst.Name(value=base_cls)) for base_cls in self._bases]
        return cst.ClassDef(
            name=cst.Name(value=self._name),
            body=cst.IndentedBlock(body=self._fields),
            bases=bases,
        )


class Module(FluentCstNode):
    def __init__(self) -> None:
        self._statements: list[FluentCstNode] = []
        self._imports: set[ImportFrom] = set()

    def add(self, node: ClassDef) -> Self:
        self._statements.append(node)
        return self

    def require_import(self, obj_name: str, from_: str) -> Self:
        self._imports.add(ImportFrom(path=from_, symbol=obj_name))
        return self

    def to_cst(self) -> cst.Module:
        body = [i.to_cst() for i in self._imports]
        body += [s.to_cst() for s in self._statements]
        return cst.Module(body=body)  # type: ignore

    def to_code(self) -> str:
        return self.to_cst().code


class ImportFrom(FluentCstNode):
    """`from mylib.types import MyType`"""

    def __init__(self, path: str, symbol: str) -> None:
        self._path = path
        self._symbol = symbol

    def to_cst(self) -> cst.SimpleStatementLine:
        return cst.SimpleStatementLine(
            body=[
                cst.ImportFrom(
                    module=_name_or_attr(self._path),
                    names=[cst.ImportAlias(name=cst.Name(value=self._symbol))],
                )
            ]
        )

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, ImportFrom)
            and self._path == other._path
            and self._symbol == other._symbol
        )

    def __hash__(self) -> int:
        return hash(self._path + self._symbol)


@overload
def _value(v: str) -> String:
    ...


@overload
def _value(v: int) -> Integer:
    ...


@overload
def _value(v: bool) -> Boolean:
    ...


@overload
def _value(v: dict[str, str]) -> Dict:
    ...


@overload
def _value(v: Call) -> Call:
    ...


@overload
def _value(v: Dict) -> Dict:
    ...


@overload
def _value(v: Attribute) -> Attribute:
    ...


@overload
def _value(v: Name) -> Name:
    ...


@overload
def _value(v: RawNode) -> RawNode:
    ...


@overload
def _value(v: list[str | Call]) -> List:
    ...


@overload
def _value(v: list[RawNode]) -> List:
    ...


def _value(v):
    # TODO(povilas): can we wrap str | int | bool into smth like Primitive?
    match v:
        case str():
            return String(v)
        case bool():
            return Boolean(v)
        case int():
            return Integer(v)
        case dict():
            return Dict().from_dict(v)
        case list():
            return List(v)
        case Call() | Dict() | Attribute() | Name() | RawNode():
            return v
        case _:
            raise Exception(f"Unexpected value {v} of type {type(v)}")


def _subscript(
    value_node: cst.BaseExpression, index_node: cst.BaseExpression
) -> cst.Subscript:
    return cst.Subscript(
        value=value_node,
        slice=[cst.SubscriptElement(slice=cst.Index(value=index_node))],
    )


def _name_or_attr(symbol: str) -> cst.Attribute | cst.Name:
    node = Attribute(symbol).to_cst() if "." in symbol else cst.Name(value=symbol)
    # Technically Attribute.to_cst() can produce BinaryOperation, but not in here.
    assert isinstance(node, cst.Attribute | cst.Name)
    return node
