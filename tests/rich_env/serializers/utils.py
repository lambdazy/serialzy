import tempfile
from typing import Any

from serialzy.api import Serializer
from serialzy.serializers.base_model import ModelBaseSerializer


def serialize_and_deserialize(serializer: Serializer, var: Any) -> Any:
    with tempfile.TemporaryFile() as file:
        serializer.serialize(var, file)
        file.flush()
        file.seek(0)
        deserialized = serializer.deserialize(file)
    return deserialized


def serialize_and_deserialize_with_meta(model_serializer: ModelBaseSerializer, var: Any) -> Any:
    with tempfile.TemporaryDirectory(suffix='serialzy_models_tests') as dest_dir:
        model_serializer.serialize_with_meta(var, dest_dir, 'model')
        deserialized = model_serializer.deserialize_with_meta(dest_dir, 'model')
    return deserialized


def to_numpy(tensor: Any) -> Any:
    return tensor.detach().cpu().numpy() if tensor.requires_grad else tensor.cpu().numpy()
