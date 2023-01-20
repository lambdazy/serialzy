import dataclasses
import importlib
import json
import logging
from abc import ABC
from io import BytesIO
from packaging import version
from typing import Any, BinaryIO, Type, Optional, Dict, cast, Union, Callable, Tuple, List

from serialzy.serializers.ellipsis import EllipsisSerializer
from serialzy.utils import cached_installed_packages
from typing_extensions import get_args, get_origin

from serialzy.api import Serializer, SerializerRegistry, Schema, VersionBoundary
from serialzy.types import EmptyListContent, get_type
from serialzy.version import __version__

_LOG = logging.getLogger(__name__)


class SequenceSerializerBase(Serializer, ABC):
    SUPPORTED_TYPES = {list, tuple}
    SCHEMA_FORMAT = "serialzy_sequence_schema"

    def __init__(self, registry: SerializerRegistry):
        self._registry = registry

    def _serialize(self, obj: Any, dest: BinaryIO) -> None:
        length = len(obj)
        dest.write(length.to_bytes(length=8, byteorder='little', signed=False))

        args = get_args(get_type(obj))
        serializers = self.__serializers_from_type_args(args)

        for i in range(len(obj)):
            with BytesIO() as handle:
                if len(serializers) == 1:
                    cast(Serializer, serializers[0]).serialize(obj[i], handle)
                else:
                    cast(Serializer, serializers[i]).serialize(obj[i], handle)
                handle.flush()

                serialized_value = handle.getvalue()
                elem_size = len(serialized_value)
                dest.write(elem_size.to_bytes(length=8, byteorder='little', signed=False))
                dest.write(serialized_value)

    def _deserialize(self, source: BinaryIO, schema_type: Type, user_type: Optional[Type] = None) -> Any:
        self._check_types_valid(schema_type, user_type)

        length = int.from_bytes(source.read(8), byteorder='little', signed=False)
        args = get_args(schema_type)
        serializers = self.__serializers_from_type_args(args)

        result = list()
        for i in range(length):
            elem_length = int.from_bytes(source.read(8), byteorder='little', signed=False)
            with BytesIO() as handle:
                handle.write(source.read(elem_length))
                handle.flush()
                handle.seek(0)

                if len(serializers) == 1:
                    obj = cast(Serializer, serializers[0]).deserialize(handle)
                else:
                    obj = cast(Serializer, serializers[i]).deserialize(handle)
                result.append(obj)

        return get_origin(schema_type)(result)  # type: ignore

    def available(self) -> bool:
        return True

    def meta(self) -> Dict[str, str]:
        return {'serialzy': __version__}

    def schema(self, typ: Type) -> Schema:
        args: Tuple[Type, ...] = get_args(typ)
        # noinspection PyProtectedMember,PyUnresolvedReferences
        schema_dict = {
            "origin": {
                "module": typ.__module__,
                "name": typ.__name__ if hasattr(typ, "__name__") else typ._name  # for typing.List
            },
            "args": [dataclasses.asdict(cast(Serializer, self._registry.find_serializer_by_type(arg)).schema(arg)) for
                     arg in args]
        }
        return Schema(self.data_format(), self.SCHEMA_FORMAT, json.dumps(schema_dict), self.meta())

    def resolve(self, schema: Schema) -> Type:
        self._validate_schema(schema)
        if schema.schema_format != self.SCHEMA_FORMAT:
            raise ValueError(f'Invalid schema format {schema.schema_format}')

        if 'serialzy' not in schema.meta:
            _LOG.warning('No serialzy version in meta')
        elif version.parse(schema.meta['serialzy']) > version.parse(cached_installed_packages["serialzy"]):
            _LOG.warning(f'Installed version of serialzy {cached_installed_packages["serialzy"]} '
                         f'is older than used for serialization {schema.meta["serialzy"]}')

        schema_dict = json.loads(schema.schema_content)
        origin = schema_dict["origin"]
        typ = getattr(importlib.import_module(origin["module"]), origin["name"])
        schemas = [Schema(**arg) for arg in schema_dict["args"]]

        if typ == List:
            serializer = cast(Serializer, self._registry.find_serializer_by_data_format(schemas[0].data_format))
            arg_type = serializer.resolve(schemas[0])
            return typ[arg_type]  # type: ignore
        else:  # tuple
            if len(schemas) == 2 and schemas[1].data_format == EllipsisSerializer.ellipsis_data_format:
                serializer = cast(Serializer, self._registry.find_serializer_by_data_format(schemas[0].data_format))
                arg_type = serializer.resolve(schemas[0])
                return typ[arg_type, ...]  # type: ignore
            else:
                typ_args = tuple(
                    cast(Serializer, self._registry.find_serializer_by_data_format(s.data_format)).resolve(s) for s in
                    schemas)
                return typ[typ_args]  # type: ignore

    def requirements(self) -> Dict[str, VersionBoundary]:
        return {}

    def __serializers_from_type_args(self, args: Tuple[Any, ...]) -> List[Serializer]:
        serializers: List[Serializer]
        if (len(args) == 2 and args[1] == Ellipsis) or len(args) == 1:  # tuple with ellipsis or list
            serializers = [cast(Serializer, self._registry.find_serializer_by_type(args[0]))]
        else:
            serializers = [cast(Serializer, self._registry.find_serializer_by_type(arg)) for arg in args]
        return serializers


class SequenceSerializerStable(SequenceSerializerBase):
    def supported_types(self) -> Union[Type, Callable[[Type], bool]]:
        return lambda t: get_origin(t) in self.SUPPORTED_TYPES and self.__check_arg(get_args(t))

    def stable(self) -> bool:
        return True

    def __check_arg(self, args: Tuple[Any, ...]) -> bool:
        if len(args) == 0:
            return False
        elif args[0] == EmptyListContent:
            return True

        for arg in args:
            serializer = self._registry.find_serializer_by_type(arg)
            if serializer is None or not serializer.available() or not serializer.stable():
                return False
        return True

    def data_format(self) -> str:
        return "serialzy_sequence_stable"


class SequenceSerializerUnstable(SequenceSerializerBase):
    def supported_types(self) -> Union[Type, Callable[[Type], bool]]:
        return lambda t: get_origin(t) in self.SUPPORTED_TYPES and self.__check_arg(get_args(t))

    def stable(self) -> bool:
        return False

    def __check_arg(self, args: Tuple[Any, ...]) -> bool:
        if len(args) == 0:
            return False
        elif args[0] == EmptyListContent:
            return False

        for arg in args:
            serializer = self._registry.find_serializer_by_type(arg)
            if serializer is None or not serializer.available():
                return False
        return True

    def data_format(self) -> str:
        return "serialzy_sequence_unstable"
