import inspect
from os import PathLike
from pathlib import Path
from typing import Type, Any, BinaryIO, Optional, Union

from serialzy.serializers.base_model import (
    ModelBaseSerializer,
    serialize_to_dir,
    deserialize_from_dir,
    unpack_model_tar
)


# noinspection PyPackageRequirements
class TensorflowKerasSerializer(ModelBaseSerializer):
    def __init__(self):
        super().__init__("keras", __name__)

    def unpack_model(self, source: BinaryIO, dest_dir: Union[str, PathLike]) -> PathLike:
        model_path = Path(dest_dir) / "model.savedmodel"
        unpack_model_tar(source, model_path)
        return model_path

    def data_format(self) -> str:
        return "tf_keras"

    def _serialize(self, obj: Any, dest: BinaryIO) -> None:
        import tensorflow as tf  # type: ignore
        serialize_to_dir(dest, lambda x: tf.keras.models.save_model(obj, x, save_format='tf'))

    def _deserialize(self, source: BinaryIO, schema_type: Type, user_type: Optional[Type] = None) -> Any:
        self._check_types_valid(schema_type, user_type)
        import tensorflow as tf  # type: ignore
        return deserialize_from_dir(source, lambda x: tf.keras.models.load_model(x))

    def _types_filter(self, typ: Type):
        import tensorflow as tf  # type: ignore
        return typ in [tf.keras.Sequential] or (inspect.isclass(typ) and issubclass(typ, tf.keras.Model))


# noinspection PyPackageRequirements
class TensorflowPureSerializer(ModelBaseSerializer):
    def __init__(self):
        super().__init__("tensorflow", __name__)

    def unpack_model(self, source: BinaryIO, dest_dir: Union[str, PathLike]) -> PathLike:
        model_path = Path(dest_dir) / "model.savedmodel"
        unpack_model_tar(source, model_path)
        return model_path

    def data_format(self) -> str:
        return "tf_pure"

    def _serialize(self, obj: Any, dest: BinaryIO) -> None:
        import tensorflow as tf  # type: ignore
        serialize_to_dir(dest, lambda x: tf.saved_model.save(obj, x))

    def _deserialize(self, source: BinaryIO, schema_type: Type, user_type: Optional[Type] = None) -> Any:
        self._check_types_valid(schema_type, user_type)
        import tensorflow as tf  # type: ignore
        return deserialize_from_dir(source, lambda x: tf.saved_model.load(x))

    def _types_filter(self, typ: Type):
        import tensorflow as tf  # type: ignore
        return typ in [tf.train.Checkpoint] or (inspect.isclass(typ) and issubclass(typ, tf.Module))
