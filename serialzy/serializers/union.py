import dataclasses
import json
import logging
import tempfile
from abc import ABC
from typing import Type, Dict, Union, BinaryIO, Any, cast, Optional, Callable, Tuple

from packaging import version  # type: ignore
from typing_extensions import get_args, get_origin

from serialzy.api import Serializer, Schema, SerializerRegistry, VersionBoundary
from serialzy.utils import cached_installed_packages
from serialzy.version import __version__

_LOG = logging.getLogger(__name__)


class UnionSerializerBase(Serializer, ABC):
    SCHEMA_FORMAT = "serialzy_union_schema"

    def __init__(self, registry: SerializerRegistry):
        self._registry = registry

    def serialize(self, obj: Any, dest: BinaryIO) -> None:
        typ = type(obj)
        serializer = self._registry.find_serializer_by_type(typ)
        if serializer is None:
            raise ValueError(f'Cannot find serializer for type {typ}')
        serializer.serialize(obj, dest)

    def _serialize(self, obj: Any, dest: BinaryIO) -> None:
        """
        Don't use this method for union serialization
        """

    def _deserialize(self, source: BinaryIO, schema_type: Type, user_type: Optional[Type] = None) -> Any:
        if user_type is None or get_origin(user_type) != Union:
            serializer = cast(Serializer, self._registry.find_serializer_by_type(schema_type))
            return serializer._deserialize(source, schema_type, user_type)
        else:
            args = get_args(user_type)
            # Optional case
            if len(args) == 2 and args[1] == type(None):
                if schema_type == type(None):
                    return cast(Serializer, self._registry.find_serializer_by_type(schema_type))._deserialize(source,
                                                                                                              schema_type)
                else:
                    try:
                        return cast(Serializer, self._registry.find_serializer_by_type(args[0]))._deserialize(source,
                                                                                                              schema_type,
                                                                                                              args[0])
                    except:
                        raise ValueError(f'Cannot deserialize data into type {user_type}')
            # General union case
            else:
                with tempfile.NamedTemporaryFile('wb+') as handle:
                    # copy source
                    while True:
                        data = source.read(8096)
                        if not data:
                            break
                        handle.write(data)

                    handle.flush()
                    handle.seek(0)

                    # try to deserialize in union arguments
                    for arg in args:
                        # noinspection PyBroadException
                        try:
                            serializer_by_type = cast(Serializer, self._registry.find_serializer_by_type(arg))
                            obj = serializer_by_type._deserialize(cast(BinaryIO, handle), schema_type, arg)
                            return obj
                        except:
                            handle.seek(0)
                            continue

                    raise ValueError(f'Cannot deserialize data into type {user_type}')

    def available(self) -> bool:
        return True

    def meta(self) -> Dict[str, str]:
        return {'serialzy': __version__}

    def schema(self, typ: Type) -> Schema:
        args = get_args(typ)
        schemas = [dataclasses.asdict(cast(Serializer, self._registry.find_serializer_by_type(x)).schema(x))
                   for x in args]
        return Schema(self.data_format(), self.SCHEMA_FORMAT, json.dumps(schemas), self.meta())

    def resolve(self, schema: Schema) -> Type:
        if schema.data_format == self.data_format():
            self._validate_schema(schema)
            if schema.schema_format != self.SCHEMA_FORMAT:
                raise ValueError(f'Invalid schema format {schema.schema_format}')

            if 'serialzy' not in schema.meta:
                _LOG.warning('No serialzy version in meta')
            elif version.parse(schema.meta['serialzy']) > version.parse(cached_installed_packages["serialzy"]):
                _LOG.warning(f'Installed version of serialzy {cached_installed_packages["serialzy"]} '
                             f'is older than used for serialization {schema.meta["serialzy"]}')

            schemas = json.loads(schema.schema_content)
            types = tuple(
                cast(Serializer, self._registry.find_serializer_by_data_format(Schema(**x).data_format))
                .resolve(Schema(**x)) for x in schemas
            )
            return cast(Type, Union[types])

        serializer = self._registry.find_serializer_by_data_format(schema.data_format)
        if serializer is None:
            raise ValueError(f'Cannot find serializer for data format {schema.data_format}')
        return serializer.resolve(schema)

    def requirements(self) -> Dict[str, VersionBoundary]:
        return {}


class UnionSerializerStable(UnionSerializerBase):
    def supported_types(self) -> Union[Type, Callable[[Type], bool]]:
        return lambda t: get_origin(t) == Union and self.__check_args(get_args(t))

    def stable(self) -> bool:
        return True

    def __check_args(self, args: Tuple[Any, ...]) -> bool:
        for arg in args:
            serializer = self._registry.find_serializer_by_type(arg)
            if serializer is None or not serializer.available() or not serializer.stable():
                return False
        return True

    def data_format(self) -> str:
        return "serialzy_union_stable"


class UnionSerializerUnstable(UnionSerializerBase):
    def supported_types(self) -> Union[Type, Callable[[Type], bool]]:
        return lambda t: get_origin(t) == Union and self.__check_args(get_args(t))

    def stable(self) -> bool:
        return False

    def __check_args(self, args: Tuple[Any, ...]) -> bool:
        all_stable = True
        for arg in args:
            serializer = self._registry.find_serializer_by_type(arg)
            if serializer is None or not serializer.available():
                return False
            all_stable = all_stable and serializer.stable()
        return not all_stable

    def data_format(self) -> str:
        return "serialzy_union_unstable"
