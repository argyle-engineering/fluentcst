from textwrap import dedent

import fluentcst as fcst

def test_multiple_classes():
    module = (
        fcst.Module()
        .add(fcst.ClassDef("Cls1").field(f1="v1"))
        .add(fcst.ClassDef("Cls2").field(f1="v1"))
    )

    assert module.to_code() == dedent("""\
        class Cls1:
            f1 = "v1"
        class Cls2:
            f1 = "v1"
    """)

def test_require_import():
    module = (
        fcst.Module()
        .require_import("Error", "lib.types.exceptions")
        .add(fcst.ClassDef("Cls1"))
    )

    assert module.to_code() == dedent("""\
        from lib.types.exceptions import Error
        class Cls1:
            pass
    """)
