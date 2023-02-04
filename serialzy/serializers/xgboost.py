from typing import BinaryIO, Type, Any, Optional

from packaging import version  # type: ignore

from serialzy.serializers.base_model import ModelBaseSerializer, serialize_to_file, deserialize_from_file


# noinspection PyPackageRequirements
class XGBoostSerializer(ModelBaseSerializer):
    def __init__(self):
        super().__init__("xgboost", __name__)

    def _serialize(self, obj: Any, dest: BinaryIO) -> None:
        serialize_to_file(dest, lambda x: obj.save_model(x))

    def _deserialize(self, source: BinaryIO, schema_type: Type, user_type: Optional[Type] = None) -> Any:
        self._check_types_valid(schema_type, user_type)
        import xgboost  # type: ignore

        def load_model(filename):
            model = xgboost.Booster({'nthread': 4})
            model.load_model(filename)
            return model

        return deserialize_from_file(source, load_model)

    def _types_filter(self, typ) -> bool:
        import xgboost as xgb  # type: ignore
        return typ in [xgb.XGBRanker, xgb.XGBRegressor, xgb.XGBClassifier]

    def data_format(self) -> str:
        return "xgb"
