[![Pypi version](https://img.shields.io/pypi/v/serialzy)](https://pypi.org/project/serialzy/)
[![Tests](https://github.com/lambdazy/serialzy/actions/workflows/tests.yaml/badge.svg)](https://github.com/lambda-zy/lzy/actions/workflows/tests.yaml)
[![Python tests coverage](https://gist.githubusercontent.com/mrMakaronka/74a3e00f914bb55c0f3582a7d48e3bcd/raw/main-coverage.svg)](https://github.com/lambdazy/lzy/tree/master/pylzy/tests)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/serialzy.svg)](https://pypi.org/project/serialzy/)

# serialzy

Serialzy is a library for python objects serialization into portable and interoperable data formats (if possible).

### Examples

Serialization:

```python
from serialzy.registry import DefaultSerializerRegistry

obj = MyObjToSerialize()

registry = DefaultSerializerRegistry()
serializer = registry.find_serializer_by_type(type(obj))
with open('result', 'wb') as file:
    serializer.serialize(obj, file)
```

Deserialization:

```python
with open('result', 'rb') as file:
    deserialized_obj = serializer.deserialize(file)
```

Serializers can be stable (with portable data formats) or unstable, e.g., cloudpickle:

```python
serializer.stable()
```

### List of supported libraries for stable serialization:

| Library                         | Types                                                                                                                                                                                                                                                                                | Data format                                                                      | 
|---------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| [CatBoost](https://catboost.ai) | [CatBoostRegressor](https://catboost.ai/en/docs/concepts/python-reference_catboostregressor), [CatBoostClassifier](https://catboost.ai/en/docs/concepts/python-reference_catboostclassifier), [CatBoostRanker](https://catboost.ai/en/docs/concepts/python-reference_catboostranker) | [cbm](https://catboost.ai/en/docs/concepts/python-reference_catboost_save_model) |
| [CatBoost](https://catboost.ai)                    | [Pool](https://catboost.ai/en/docs/concepts/python-reference_pool)                                                                                                                                                                                                                                                                             | [quantized pool](https://catboost.ai/en/docs/concepts/python-reference_pool_save)                                                               |