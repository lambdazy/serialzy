[![Pypi version](https://img.shields.io/pypi/v/serialzy)](https://pypi.org/project/serialzy/)
[![Tests](https://github.com/lambdazy/serialzy/actions/workflows/tests.yaml/badge.svg)](https://github.com/lambda-zy/lzy/actions/workflows/tests.yaml)
[![Python tests coverage](https://gist.githubusercontent.com/mrMakaronka/74a3e00f914bb55c0f3582a7d48e3bcd/raw/main-coverage.svg)](https://github.com/lambdazy/lzy/tree/master/pylzy/tests)


# serialzy

Serialzy is a library for python objects serialization into portable and interoperable data formats (if possible).

Serialization example:

```python
from serialzy.registry import DefaultSerializerRegistry

obj = MyObjToSerialize()

registry = DefaultSerializerRegistry()
serializer = self.registry.find_serializer_by_type(type(obj))
with open('result', 'wb') as file:
    serializer.serialize(obj, file)
```

Deserialization example:

```python
with open('result', 'rb') as file:
    deserialized_obj = serializer.deserialize(file, type(obj))
```

Serializers also provide data schema:

```python
serializer = self.registry.find_serializer_by_name('serializer_name')
schema = serializer.schema(type(obj))
```

Schema can be turned into python type:

```python
serializer = self.registry.find_serializer_by_name('serializer_name')
typ = serialzier.resolve(schema)
```
