import tempfile
from typing import Any

from serialzy.api import Serializer


def serialized_and_deserialized(serializer: Serializer, var: Any) -> Any:
    with tempfile.TemporaryFile() as file:
        serializer.serialize(var, file)
        file.flush()
        file.seek(0)
        deserialized = serializer.deserialize(file, type(var))
    return deserialized
