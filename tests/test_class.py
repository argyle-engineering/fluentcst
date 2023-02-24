from textwrap import dedent

import fluentcst as fcst

def test_field_can_be_fluent_dict():
    code = (
        fcst.ClassDef("Cls1")
        .field(f1=fcst.Dict().element("d1", "v1"))
        .to_code()
    )
    assert code == dedent("""\
        class Cls1:
            f1 = {"d1": "v1"}
    """)
