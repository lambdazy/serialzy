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
class LightGBMSerializer(ModelBaseSerializer):
    def __init__(self):
        super().__init__("lightgbm", __name__)

    def unpack_model(self, source: BinaryIO, dest_dir: Union[str, PathLike]) -> PathLike:
        model_path = Path(dest_dir) / "model"
        unpack_model_file(source, model_path)
        return model_path

    def _serialize(self, obj: Any, dest: BinaryIO) -> None:
        serialize_to_file(dest, lambda x: obj.booster_.save_model(x))

    def _deserialize(self, source: BinaryIO, schema_type: Type, user_type: Optional[Type] = None) -> Any:
        self._check_types_valid(schema_type, user_type)
        import lightgbm  # type: ignore
        return deserialize_from_file(source, lambda x: lightgbm.Booster(model_file=x))

    def _types_filter(self, typ: Type) -> bool:
        import lightgbm as lgbm  # type: ignore
        return typ in [lgbm.LGBMRanker, lgbm.LGBMRegressor, lgbm.LGBMClassifier]

    def data_format(self) -> str:
        return "lgbm"
