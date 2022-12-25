import logging
from typing import Any, BinaryIO, Callable, Dict, Type, Union, Optional

from packaging import version  # type: ignore

from serialzy.api import StandardDataFormats, VersionBoundary
from serialzy.base import DefaultSchemaSerializerByReference
from serialzy.version import __version__

_LOG = logging.getLogger(__name__)


# noinspection PyPackageRequirements
class PrimitiveSerializer(DefaultSchemaSerializerByReference):
    def _serialize(self, obj: Any, dest: BinaryIO) -> None:
        dumps = str(obj).encode("utf-8")
        dest.write(dumps)

    def _deserialize(self, source: BinaryIO, schema_type: Type, user_type: Optional[Type] = None) -> Any:
        self._check_types_valid(schema_type, user_type)
        read = source.read().decode("utf-8")
        if schema_type == type(None):
            return None
        elif schema_type == bool:
            return read == "True"
        return schema_type(read)

    def supported_types(self) -> Union[Type, Callable[[Type], bool]]:
        return lambda t: t in [int, float, str, bool, type(None)]

    def available(self) -> bool:
        return True

    def stable(self) -> bool:
        return True

    def data_format(self) -> str:
        return StandardDataFormats.primitive_type.name

    def meta(self) -> Dict[str, str]:
        return {'serialzy': __version__}

    def requirements(self) -> Dict[str, VersionBoundary]:
        return {}
