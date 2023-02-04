import inspect
from typing import BinaryIO, Type, Any, Optional

from packaging import version  # type: ignore

from serialzy.serializers.base_model import ModelBaseSerializer, serialize_to_file, deserialize_from_file


# noinspection PyPackageRequirements
class TorchSerializer(ModelBaseSerializer):
    def __init__(self):
        super().__init__("torch", __name__)

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
