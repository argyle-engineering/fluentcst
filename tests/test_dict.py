import fluentcst as fcst


def test_only_string():
    code = fcst.Dict().element("f1", "v1").element("f2", "v2").to_code()
    assert code == '{"f1": "v1", "f2": "v2"}'


def test_integer_fields():
    assert fcst.Dict.from_dict({"f1": 1}).to_code() == '{"f1": 1}'


def test_none_value():
    code = fcst.Dict.from_dict({"f1": None}).to_code()
    assert code == '{"f1": None}'


def test_attribute_value():
    code = fcst.Dict().element("f1", fcst.Attribute("Person.name")).to_code()
    assert code == '{"f1": Person.name}'


def test_nesting():
    code = fcst.Dict.from_dict({"f1": {"f2": "v2"}, "f3": "v3"}).to_code()
    assert code == '{"f1": {"f2": "v2"}, "f3": "v3"}'
