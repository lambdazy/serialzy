import logging
import inspect
from typing import Any, BinaryIO, Callable, Dict, Type, Union, Optional

from serialzy.api import StandardDataFormats, Schema, VersionBoundary
from serialzy.base import DefaultSchemaSerializerByValue
from serialzy.utils import cached_installed_packages
from packaging import version  # type: ignore

_LOG = logging.getLogger(__name__)


# noinspection PyMethodMayBeStatic
class ProtoMessageSerializer(DefaultSchemaSerializerByValue):
    def _serialize(self, obj: Any, dest: BinaryIO) -> None:
        obj.dump(dest)

    def _deserialize(self, source: BinaryIO, schema_type: Type, user_type: Optional[Type] = None) -> Any:
        from pure_protobuf.dataclasses_ import load, Message  # type: ignore

        if user_type is not None:
            if not issubclass(user_type, Message):
                raise ValueError(f'Cannot deserialize data with schema type {schema_type} into type {user_type}')
            # noinspection PyTypeChecker
            return load(user_type, source)

        # noinspection PyTypeChecker
        return load(schema_type, source)

    def available(self) -> bool:
        base_available = super().available()
        if not base_available:
            return False

        # noinspection PyBroadException
        try:
            import pure_protobuf  # type: ignore
            return True
        except:
            return False

    def stable(self) -> bool:
        return True

    def supported_types(self) -> Union[Type, Callable[[Type], bool]]:
        return lambda t: self._check_is_message(t)

    def data_format(self) -> str:
        return StandardDataFormats.proto.name

    def meta(self) -> Dict[str, str]:
        return {"pure-protobuf": cached_installed_packages["pure-protobuf"]}

    def resolve(self, schema: Schema) -> Type:
        typ = super().resolve(schema)
        if 'pure-protobuf' not in schema.meta:
            _LOG.warning('No pure-protobuf version in meta')
        elif version.parse(schema.meta['pure-protobuf']) > version.parse(cached_installed_packages["pure-protobuf"]):
            _LOG.warning(f'Installed version of pure-protobuf {cached_installed_packages["pure-protobuf"]} '
                         f'is older than used for serialization {schema.meta["pure-protobuf"]}')
        return typ

    def requirements(self) -> Dict[str, VersionBoundary]:
        return {'pure-protobuf': VersionBoundary()}

    def _check_is_message(self, obj: Any) -> bool:
        from pure_protobuf.dataclasses_ import Message  # type: ignore
        try:
            return inspect.isclass(obj) and issubclass(obj, Message)
        except TypeError:
            # for some reason `inspect.isclass(list[str])` returns true,
            # but `issubclass(list[str], Message)` raises TypeError
            return False
