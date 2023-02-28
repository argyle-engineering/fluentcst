# fluentcst

An ergonomic interface for [libCST](https://github.com/Instagram/LibCST):

```py
import fluentcst as fcst

module = fcst.Module()
module.require_import("BaseModel", from_="pydantic")
module.add(
    fcst.ClassDef("MyModel")
    .base("BaseModel")
    .field(version="1.2.3")
    .field(status={"code": "200", "message": "OK"})
    .field(items=[fcst.Call("Item", name="i1", value="v1")])
)
print(module.to_code())
```

that builds valid Python code:

```py
from pydantic import BaseModel

class MyModel(BaseModel):
    version = "1.2.3"
    status = {"code": "200", "message": "OK"}
    items = [Item(name = "i1", value = "v1")]
```

Highly Work in Progress. Expect interface to break, a lot.
