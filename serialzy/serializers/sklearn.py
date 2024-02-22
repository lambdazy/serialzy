from os import PathLike
from pathlib import Path
from typing import BinaryIO, Tuple, Type, Any, Optional, Union

import pickle
from serialzy.serializers.base_model import (
    ModelBaseSerializer,
    serialize_to_file,
    deserialize_from_file,
    unpack_model_file
)


class SciKitLearnSerializer(ModelBaseSerializer):
    def __init__(self):
        super().__init__("sklearn", __name__, package="scikit-learn")

    def unpack_model(self, source: BinaryIO, dest_dir: Union[str, PathLike]) -> PathLike:
        model_path = Path(dest_dir) / "model.pickle"
        unpack_model_file(source, model_path)
        return model_path

    def _serialize(self, obj: Any, dest: BinaryIO) -> None:
        if not isinstance(obj, self._get_supported_types()):
            raise ValueError(f"Attempt to serialize unsupported SciKit-Learn model {__name__}")

        def save_model(filename):
            with open(filename, "wb") as f:
                pickle.dump(obj, f)

        serialize_to_file(dest, save_model)

    def _deserialize(self, source: BinaryIO, schema_type: Type, user_type: Optional[Type] = None) -> Any:
        self._check_types_valid(schema_type, user_type)

        def load_model(filename):
            with open(filename, "rb") as f:
                skl_model = pickle.load(f)
                return skl_model

        return deserialize_from_file(source, load_model)

    def _types_filter(self, typ: Type) -> bool:
        return typ in self._get_supported_types()

    def data_format(self) -> str:
        return 'skl'

    @staticmethod
    def _get_supported_types() -> Tuple[Type, ...]:
        import sklearn.ensemble as skle  # type: ignore
        return (
            skle.GradientBoostingClassifier,
            skle.GradientBoostingRegressor,
            skle.IsolationForest,
            skle.RandomForestRegressor,
            skle.ExtraTreesClassifier,
            skle.ExtraTreesRegressor,
        )
