import tempfile
from typing import Any

from serialzy.api import Serializer


def serialize_and_deserialize(serializer: Serializer, var: Any) -> Any:
    with tempfile.TemporaryFile() as file:
        serializer.serialize(var, file)
        file.flush()
        file.seek(0)
        deserialized = serializer.deserialize(file)
    return deserialized
