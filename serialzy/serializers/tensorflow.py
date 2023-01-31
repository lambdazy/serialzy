import inspect
from typing import Union, Type, Callable, Any, BinaryIO, Optional

from serialzy.serializers.base_model import ModelBaseSerializer, serialize_to_dir, deserialize_from_dir


# noinspection PyPackageRequirements
class TensorflowKerasSerializer(ModelBaseSerializer):
    def __init__(self):
        super().__init__("tensorflow", __name__)

    def supported_types(self) -> Union[Type, Callable[[Type], bool]]:
        import tensorflow as tf  # type: ignore
        return lambda t: t in [tf.keras.Sequential] or (inspect.isclass(t) and issubclass(t, tf.keras.Model))

    def data_format(self) -> str:
        return "tf_keras"

    def _serialize(self, obj: Any, dest: BinaryIO) -> None:
        serialize_to_dir(dest, lambda x: obj.save(x, save_format=self.data_format()))

    def _deserialize(self, source: BinaryIO, schema_type: Type, user_type: Optional[Type] = None) -> Any:
        self._check_types_valid(schema_type, user_type)
        import tensorflow as tf  # type: ignore
        return deserialize_from_dir(source, lambda x: tf.keras.models.load_model(x))


# noinspection PyPackageRequirements
class TensorflowPureSerializer(ModelBaseSerializer):
    def __init__(self):
        super().__init__("tensorflow", __name__)

    def supported_types(self) -> Union[Type, Callable[[Type], bool]]:
        import tensorflow as tf  # type: ignore
        return lambda t: t in [tf.train.Checkpoint] or (inspect.isclass(t) and issubclass(t, tf.Module))

    def data_format(self) -> str:
        return "tf_pure"

    def _serialize(self, obj: Any, dest: BinaryIO) -> None:
        import tensorflow as tf  # type: ignore
        serialize_to_dir(dest, lambda x: tf.saved_model.save(obj, x))

    def _deserialize(self, source: BinaryIO, schema_type: Type, user_type: Optional[Type] = None) -> Any:
        self._check_types_valid(schema_type, user_type)
        import tensorflow as tf  # type: ignore
        return deserialize_from_dir(source, lambda x: tf.saved_model.load(x))
