import libcst as cst
import fluentcst as fcst


def test_in_list():
    node = fcst.List(
        [
            fcst.RawNode(
                cst.Call(
                    func=cst.Name(value="assert_is_some"),
                    args=[cst.Arg(value=cst.Name(value="obj"))],
                )
            )
        ]
    )

    assert node.to_code() == "[assert_is_some(obj)]\n"
