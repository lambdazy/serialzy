import sys
from typing import Any, BinaryIO, Type, Optional, Union, Callable, Dict

from serialzy.api import VersionBoundary, Serializer, Schema, StandardSchemaFormats
from serialzy.version import __version__


class EllipsisSerializer(Serializer):
    ellipsis_data_format = "serialzy_python_ellipsis"

    def _serialize(self, obj: Any, dest: BinaryIO) -> None:
        pass

    def _deserialize(self, source: BinaryIO, schema_type: Type, user_type: Optional[Type] = None) -> Any:
        self._check_types_valid(schema_type, user_type)
        return schema_type

    def supported_types(self) -> Union[Type, Callable[[Type], bool]]:
        # noinspection PyTypeChecker
        return lambda x: x == Ellipsis  # type: ignore

    def available(self) -> bool:
        return True

    def stable(self) -> bool:
        return True

    def data_format(self) -> str:
        return self.ellipsis_data_format

    def meta(self) -> Dict[str, str]:
        version = sys.version_info
        return {
            'serialzy': __version__,
            'python': f"{version.major}.{version.minor}.{version.micro}"
        }

    def requirements(self) -> Dict[str, VersionBoundary]:
        return {}

    def schema(self, typ: Type) -> Schema:
        return Schema(
            self.data_format(),
            StandardSchemaFormats.no_schema.name,
            "",
            self.meta(),
        )

    def resolve(self, schema: Schema) -> Type:
        self._validate_schema(schema)
        # noinspection PyTypeChecker
        return Ellipsis  # type: ignore
