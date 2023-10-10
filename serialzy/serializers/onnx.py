import inspect
import os
from pathlib import Path
from typing import BinaryIO, Union, Type, Optional, Any

from serialzy.serializers.base_model import (
    ModelBaseSerializer,
    deserialize_from_file,
    serialize_to_file,
    unpack_model_file
)


class ONNXSerializer(ModelBaseSerializer):
    def __init__(self):
        super().__init__("onnx", __name__)

    def _types_filter(self, typ: Type) -> bool:
        import onnx
        return inspect.isclass(typ) and issubclass(typ, onnx.ModelProto)

    def _serialize(self, obj: Any, dest: BinaryIO) -> None:
        import onnx

        if not isinstance(obj, onnx.ModelProto):
            raise ValueError(f"Attempt to serialize not an ONNX model with {__name__}")

        def write_onnx(out_filename: str) -> None:
            with open(out_filename, "wb") as f:
                f.write(obj.SerializeToString())

        serialize_to_file(dest, write_onnx)

    def _deserialize(self, source: BinaryIO, schema_type: Type, user_type: Optional[Type] = None) -> Any:
        self._check_types_valid(schema_type, user_type)

        import onnx

        def read_onnx(in_filename: str) -> onnx.ModelProto:
            with open(in_filename, "rb") as f:
                onnx_model = onnx.load(f)
                return onnx_model

        return deserialize_from_file(source, read_onnx)

    def data_format(self) -> str:
        return self.module

    def unpack_model(self, source: BinaryIO, dest_dir: Union[str, os.PathLike]) -> os.PathLike:
        model_path = Path(dest_dir) / f"model.{self.data_format()}"
        unpack_model_file(source, model_path)
        return model_path
