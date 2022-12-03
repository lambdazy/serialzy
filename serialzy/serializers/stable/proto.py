import logging
import inspect
from typing import Any, BinaryIO, Callable, Dict, Type, Union

from serialzy.api import StandardDataFormats, Schema
from serialzy.base import DefaultSchemaSerializerByValue
from serialzy.utils import cached_installed_packages
from packaging import version  # type: ignore

_LOG = logging.getLogger(__name__)


# noinspection PyMethodMayBeStatic
class ProtoMessageSerializer(DefaultSchemaSerializerByValue):
    def serialize(self, obj: Any, dest: BinaryIO) -> None:
        obj.dump(dest)

    def deserialize(self, source: BinaryIO, typ: Type) -> Any:
        from pure_protobuf.dataclasses_ import load  # type: ignore

        # noinspection PyTypeChecker
        return load(typ, source)

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
        from pure_protobuf.dataclasses_ import Message  # type: ignore

        return lambda t: inspect.isclass(t) and issubclass(t, Message)

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
