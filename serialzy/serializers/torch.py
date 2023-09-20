import inspect
from pathlib import Path
from typing import BinaryIO, Type, Any, Optional

from packaging import version  # type: ignore

from serialzy.serializers.base_model import ModelBaseSerializer, serialize_to_file, deserialize_from_file, \
    unpack_model_file


# noinspection PyPackageRequirements
class TorchSerializer(ModelBaseSerializer):
    def __init__(self):
        super().__init__("torch", __name__)

    def unpack_model(self, source: BinaryIO, dest_dir: str) -> None:
        unpack_model_file(source, Path(dest_dir) / "model.pt")

    def _serialize(self, obj: Any, dest: BinaryIO) -> None:
        import torch  # type: ignore
        serialize_to_file(dest, lambda x: torch.jit.script(obj).save(x))

    def _deserialize(self, source: BinaryIO, schema_type: Type, user_type: Optional[Type] = None) -> Any:
        self._check_types_valid(schema_type, user_type)
        import torch  # type: ignore
        return deserialize_from_file(source, lambda x: torch.jit.load(x))

    def _types_filter(self, typ: Type) -> bool:
        import torch  # type: ignore
        return inspect.isclass(typ) and issubclass(typ, torch.nn.Module)

    def data_format(self) -> str:
        return "pt"
