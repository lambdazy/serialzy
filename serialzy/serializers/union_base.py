import dataclasses
import json
import logging
from abc import ABC
from typing import Type, Dict, Union, BinaryIO, Any, cast, Optional

from packaging import version  # type: ignore
from typing_extensions import get_args

from serialzy.api import Serializer, Schema, T, SerializerRegistry
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

    def deserialize(self, source: BinaryIO, typ: Optional[Type[T]] = None) -> T:
        if typ is None:
            typ = self._deserialize_type(source)
        else:
            self._skip_header(source)

        serializer = self._registry.find_serializer_by_type(typ)
        if serializer is None:
            raise ValueError(f'Cannot find serializer for type {typ}')
        return serializer._deserialize(source, cast(Type[T], typ))

    def _deserialize(self, source: BinaryIO, typ: Type[T]) -> T:
        """
        Don't use this method for union deserialization
        """

    def available(self) -> bool:
        return True

    def data_format(self) -> str:
        return "serialzy_union"

    def meta(self) -> Dict[str, str]:
        return {'serialzy': __version__}

    def schema(self, typ: type) -> Schema:
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
