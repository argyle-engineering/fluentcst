import fluentcst as fcst


def test_strings_can_have_quotes():
    assert fcst.String('"value"').to_code() == '"\\"value\\""'
