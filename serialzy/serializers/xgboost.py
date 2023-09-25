from os import PathLike
from pathlib import Path
from typing import BinaryIO, Type, Any, Optional, Union

from serialzy.serializers.base_model import (
    ModelBaseSerializer,
    serialize_to_file,
    deserialize_from_file,
    unpack_model_file
)


# noinspection PyPackageRequirements
class XGBoostSerializer(ModelBaseSerializer):
    def __init__(self):
        super().__init__("xgboost", __name__)

    def unpack_model(self, source: BinaryIO, dest_dir: Union[str, PathLike]) -> PathLike:
        model_path = Path(dest_dir) / "model"
        unpack_model_file(source, model_path)
        return model_path

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
