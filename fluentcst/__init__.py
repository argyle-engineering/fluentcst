"""
Reference:
* https://github.com/facebookincubator/Bowler
* https://github.com/lensvol/astboom
"""

from typing import overload

import libcst as cst


class FluentCstNode:
    def to_code(self) -> str:
        # TODO(povilas): optionally use black
        cst_node = self.to_cst()
        if isinstance(cst_node, cst.List):
            # TODO(povilas): see if I can remove Expr?
            cst_node = cst.SimpleStatementLine(body=[cst.Expr(value=cst_node)])

        return cst.Module(body=[cst_node]).code

    # TODO(povilas): abstract method
    def to_cst(self) -> cst.SimpleStatementLine | cst.BaseCompoundStatement | cst.List:
        raise NotImplemented


class Assign(FluentCstNode):
    pass


class String(FluentCstNode):
    """SimpleString for now only."""

    def __init__(self, value: str) -> None:
        self._value = value

    def to_cst(self) -> cst.SimpleString:
        return cst.SimpleString(value=f'"{self._value}"')


class List(FluentCstNode):
    def __init__(self, elements: list["str | Call"]) -> None:
        self._elements = elements

    def to_cst(self) -> cst.List:
        elems = [
            cst.Element(value=String(v).to_cst() if isinstance(v, str) else v.to_cst())
            for v in self._elements
        ]
        return cst.List(elements=elems)


class Dict(FluentCstNode):
    # TODO(povilas): only dict[str, str] is supported for now
    @classmethod
    def from_dict(cls: type["Dict"], d: dict[str, str]) -> "Dict":
        dict_node = cls()
        for k, v in d.items():
            dict_node.element(k, v)
        return dict_node

    def __init__(self) -> None:
        self._elements: list[tuple[str, str]] = []

    def element(self, key: str, value: str) -> "Dict":
        self._elements.append((key, value))
        return self

    def to_cst(self) -> cst.Dict:
        dict_elems = [
            cst.DictElement(key=String(k).to_cst(), value=String(v).to_cst())
            for k, v in self._elements
        ]
        return cst.Dict(elements=dict_elems)


class Annotation(FluentCstNode):
    def __init__(self, type_name: str) -> None:
        # For a union of types
        self._types = [type_name]

    def or_(self, type_name: str) -> "Annotation":
        self._types.append(type_name)
        return self

    def to_cst(self) -> cst.Annotation:
        return cst.Annotation(_bin_or(self._types))


def _bin_or(args: list[str]) -> cst.BinaryOperation | cst.Name:
    if len(args) == 1:
        return cst.Name(value=args[0])
    else:
        return cst.BinaryOperation(
            left=cst.Name(value=args[0]),
            operator=cst.BitOr(),
            right=_bin_or(args[1:]),
        )


class Call(FluentCstNode):
    def __init__(self, name___: str, **kwargs: str) -> None:
        self._name = name___
        self._kwargs = kwargs

    def to_cst(self) -> cst.Call:
        call_args = [
            cst.Arg(value=String(v).to_cst(), keyword=cst.Name(value=k))
            for k, v in self._kwargs.items()
        ]
        return cst.Call(func=cst.Name(value=self._name), args=call_args)


class ClassDef(FluentCstNode):
    def __init__(self, name: str) -> None:
        self._name = name
        self._fields = []

    def to_cst(self) -> cst.ClassDef:
        return cst.ClassDef(
            name=cst.Name(value=self._name),
            body=cst.IndentedBlock(body=self._fields),
        )

    def field(
        self, **kwargs: str | Call | dict[str, str] | list[str | Call]
    ) -> "ClassDef":
        for k, v in kwargs.items():
            value_node = _value(v)
            field_node = cst.SimpleStatementLine(
                body=[
                    cst.Assign(
                        targets=[cst.AssignTarget(target=cst.Name(value=k))],
                        value=value_node.to_cst(),
                    )
                ]
            )
            self._fields.append(field_node)

        return self


@overload
def _value(v: str) -> String:
    ...


@overload
def _value(v: dict[str, str]) -> Dict:
    ...


@overload
def _value(v: Call) -> Call:
    ...


@overload
def _value(v: list[str | Call]) -> List:
    ...


def _value(v: str | Call | dict[str, str] | list) -> String | Dict | List | Call:
    match v:
        case str():
            return String(v)
        case dict():
            return Dict().from_dict(v)
        case list():
            return List(v)
        case Call():
            return v
        case _:
            raise Exception(f"Unexpected value {v} of type {type(v)}")
