from textwrap import dedent

import fluentcst as fcst


def test_field_can_be_fluent_dict():
    code = fcst.ClassDef("Cls1").field("f1", fcst.Dict().element("d1", "v1")).to_code()
    assert code == dedent(
        """\
        class Cls1:
            f1 = {"d1": "v1"}
    """
    )


def test_field_can_be_nested_dicts():
    code = (
        fcst.ClassDef("Cls1").field("f1", {"d1": "v1", "d2": {"d2.1": "v1"}}).to_code()
    )
    assert code == dedent(
        """\
        class Cls1:
            f1 = {"d1": "v1", "d2": {"d2.1": "v1"}}
    """
    )


def test_field_can_be_attribute_with_bitor():
    code = (
        fcst.ClassDef("Cls1")
        .field("data", fcst.Attribute("BaseCls.data").bitor({"a": "b"}))
        .to_code()
    )

    assert code == dedent(
        """\
        class Cls1:
            data = BaseCls.data | {"a": "b"}
    """
    )


def test_field_with_only_type_declaration():
    code = fcst.ClassDef("Cls1").field("f1", type="int").to_code()
    assert code == dedent(
        """\
        class Cls1:
            f1: int
    """
    )


def test_field_with_list_type():
    code = fcst.ClassDef("Cls1").field("f1", type=["int"]).to_code()
    assert code == dedent(
        """\
        class Cls1:
            f1: list[int]
    """
    )


def test_field_with_untyped_list():
    code = fcst.ClassDef("Cls1").field("f1", type=[]).to_code()
    assert code == dedent(
        """\
        class Cls1:
            f1: list
    """
    )
