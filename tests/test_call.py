import fluentcst as fcst


def test_no_args():
    assert fcst.Call("func").to_code() == "func()"


def test_args():
    assert fcst.Call("func", "v1", "v2").to_code() == 'func("v1", "v2")'


def test_int_args():
    assert fcst.Call("func", 1, 2).to_code() == "func(1, 2)"


def test_attribute_args():
    assert fcst.Call("func", fcst.Attribute("obj.attr1")).to_code() == "func(obj.attr1)"


def test_name_args():
    assert (
        fcst.Call("cast", fcst.Name("int"), fcst.Name("obj")).to_code()
        == "cast(int, obj)"
    )


def test_kwargs():
    assert fcst.Call("func", a1="v1", a2="v2").to_code() == 'func(a1 = "v1", a2 = "v2")'


def test_args_and_kwargs():
    assert (
        fcst.Call("func", "v1", "v2", a1="v1", a2="v2").to_code()
        == 'func("v1", "v2", a1 = "v1", a2 = "v2")'
    )


def test_boolean_kwargs():
    assert fcst.Call("func", a1="v1", a2=True).to_code() == 'func(a1 = "v1", a2 = True)'
