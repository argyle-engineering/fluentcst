import fluentcst as fcst


def test_import_from():
    node = fcst.ImportFrom("lib.module.inner", "Type")
    assert node.to_code() == "from lib.module.inner import Type"

    node = fcst.ImportFrom("lib", "Type")
    assert node.to_code() == "from lib import Type"
