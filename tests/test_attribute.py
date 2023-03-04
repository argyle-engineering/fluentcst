import fluentcst as fcst


def test_or_dict():
    assert (
        fcst.Attribute("resp.data").bitor({"a": "b"}).to_code()
        == 'resp.data | {"a": "b"}'
    )


def test_list_index():
    assert (
        fcst.Attribute("Profile.pictures[0].url").to_code() == "Profile.pictures[0].url"
    )
