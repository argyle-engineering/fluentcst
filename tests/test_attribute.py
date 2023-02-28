import fluentcst as fcst


def test_or_dict():
    assert (
        fcst.Attribute("resp.data").bitor({"a": "b"}).to_code()
        == 'resp.data | {"a": "b"}'
    )
