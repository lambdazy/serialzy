import abc
import dataclasses
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, BinaryIO, Callable, Dict, Optional, Type, TypeVar, Union, cast

from packaging import version  # type: ignore

T = TypeVar("T")

_LOG = logging.getLogger(__name__)


class StandardDataFormats(Enum):
    pickle = "pickle"
    proto = "proto"
    raw_file = "raw_file"
    primitive_type = "primitive_type"


class StandardSchemaFormats(Enum):
    pickled_type = "pickled_type"
    json_pickled_type = "json_pickled_type"
    no_schema = "no_schema"


@dataclass
class Schema:
    data_format: str
    schema_format: str
    schema_content: str = ''
    meta: Dict[str, str] = field(default_factory=lambda: {})


class Serializer(abc.ABC):
    def serialize(self, obj: Any, dest: BinaryIO) -> None:
        """
        :param obj: object to serialize into bytes
        :param dest: serialized obj is written into dest
        :return: None
        """

        # write schema header
        self._write_schema(type(obj), dest)

        # write serialized data
        self._serialize(obj, dest)

    @abc.abstractmethod
    def _serialize(self, obj: Any, dest: BinaryIO) -> None:
        """
        :param obj: object to serialize into bytes
        :param dest: serialized obj is written into dest
        :return: None
        """

    def deserialize(self, source: BinaryIO, typ: Optional[Type[T]] = None) -> T:
        """
        :param source: buffer of file with serialized data
        :param typ: type of the resulting object, fetched from the header if None
        :return: deserialized object
        """

        # read schema header
        if typ is None:
            typ = self._deserialize_type(source)
        else:
            self._skip_header(source)

        # read serialized data
        return self._deserialize(source, cast(Type[T], typ))

    @abc.abstractmethod
    def _deserialize(self, source: BinaryIO, typ: Type[T]) -> T:
        """
        :param source: buffer of file with serialized data
        :param typ: type of the resulting object
        :return: deserialized object
        """

    @abc.abstractmethod
    def supported_types(self) -> Union[Type, Callable[[Type], bool]]:
        """
        :return: type suitable for the serializer or types filter
        """

    @abc.abstractmethod
    def available(self) -> bool:
        """
        :return: True if the serializer can be used in the current environment, otherwise False
        """

    @abc.abstractmethod
    def stable(self) -> bool:
        """
        :return: True if the serializer does not depend on python version/dependency versions/etc., otherwise False
        """

    @abc.abstractmethod
    def data_format(self) -> str:
        """
        :return: data format that this serializer is working with
        """

    @abc.abstractmethod
    def meta(self) -> Dict[str, str]:
        """
        :return: meta of this serializer, e.g., versions of dependencies
        """

    @abc.abstractmethod
    def schema(self, typ: type) -> Schema:
        """
        :param typ: type of object for serialization
        :return: schema for the object
        """

    @abc.abstractmethod
    def resolve(self, schema: Schema) -> Type:
        """
        :param schema: schema that contains information about serialized data
        :return: Type used for python representation of the schema
        """

    def _validate_schema(self, schema: Schema) -> None:
        if schema.data_format != self.data_format():
            raise ValueError(
                f"Invalid data format {schema.data_format}, expected {self.data_format()}"
            )

    def _deserialize_type(self, source: BinaryIO) -> Type:
        header_len = int.from_bytes(source.read(8), byteorder='big', signed=False)
        schema_json = source.read(header_len).decode('utf-8')
        schema = Schema(**json.loads(schema_json))
        typ = self.resolve(schema)
        return typ

    @staticmethod
    def _skip_header(source: BinaryIO) -> None:
        header_len = int.from_bytes(source.read(8), byteorder='big', signed=False)
        source.read(header_len)

    def _write_schema(self, typ: Type, dest: BinaryIO) -> None:
        schema = self.schema(typ)
        schema_json = json.dumps(dataclasses.asdict(schema))
        schema_bytes = schema_json.encode('utf-8')
        header_len = len(schema_bytes)
        dest.write(header_len.to_bytes(length=8, byteorder='big', signed=False))
        dest.write(schema_bytes)


class SerializerRegistry(abc.ABC):
    @abc.abstractmethod
    def register_serializer(self, serializer: Serializer, priority: Optional[int] = None) -> None:
        """
        :param serializer: serializer to register
        :param priority: number that indicates serializer's priority: 0 - max priority
        :return: None
        """

    @abc.abstractmethod
    def unregister_serializer(self, serializer: Serializer) -> None:
        """
        :param serializer: serializer to unregister
        :return:
        """

    @abc.abstractmethod
    def find_serializer_by_type(self, typ: Type) -> Optional[Serializer]:
        """
        :param typ: python Type needed to serialize
        :return: corresponding serializer or None
        """

    @abc.abstractmethod
    def find_serializer_by_data_format(self, data_format: str) -> Optional[Serializer]:
        """
        :param data_format: data format to resolve serializer
        :return: Serializer if there is a serializer for that data format, None otherwise
        """
