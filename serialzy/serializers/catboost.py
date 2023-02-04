from typing import BinaryIO, Callable, Type, Union, Any, Optional

from packaging import version  # type: ignore

from serialzy.errors import SerialzyError
from serialzy.serializers.base_model import ModelBaseSerializer, serialize_to_file, deserialize_from_file


# noinspection PyPackageRequirements
class CatboostPoolSerializer(ModelBaseSerializer):
    def __init__(self):
        super().__init__("catboost", __name__)

    def _serialize(self, obj: Any, dest: BinaryIO) -> None:
        if not obj.is_quantized():  # type: ignore
            raise SerialzyError('Only quantized pools can be serialized')
        serialize_to_file(dest, lambda x: obj.save(x))

    def _deserialize(self, source: BinaryIO, schema_type: Type, user_type: Optional[Type] = None) -> Any:
        self._check_types_valid(schema_type, user_type)
        import catboost
        return deserialize_from_file(source, lambda x: catboost.Pool("quantized://" + x))

    def supported_types(self) -> Union[Type, Callable[[Type], bool]]:
        import catboost

        return catboost.Pool  # type: ignore

    def data_format(self) -> str:
        return "catboost_quantized_pool"


# noinspection PyPackageRequirements
class CatboostModelSerializer(ModelBaseSerializer):
    def __init__(self):
        super().__init__("catboost", __name__)

    def _serialize(self, obj: Any, dest: BinaryIO) -> None:
        serialize_to_file(dest, lambda x: obj.save_model(x, format=self.data_format()))

    def _deserialize(self, source: BinaryIO, schema_type: Type, user_type: Optional[Type] = None) -> Any:
        self._check_types_valid(schema_type, user_type)
        model = schema_type()
        return deserialize_from_file(source, lambda x: model.load_model(x, format=self.data_format()))

    def _types_filter(self, typ: Type) -> bool:
        import catboost as cb
        return typ in [cb.CatBoostClassifier, cb.CatBoostRegressor, cb.CatBoostRanker]  # type: ignore

    def data_format(self) -> str:
        return "cbm"  # CatBoost binary format https://catboost.ai/en/docs/concepts/python-reference_catboost_save_model
