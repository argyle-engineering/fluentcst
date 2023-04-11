import fluentcst as fcst


def test_strings_can_have_quotes():
    fcst.String('"value"').to_code() == '"\\"value\\""'
