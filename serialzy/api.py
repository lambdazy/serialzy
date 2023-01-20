import abc
import dataclasses
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, BinaryIO, Callable, Dict, Optional, Type, Union

from packaging import version  # type: ignore

from serialzy.types import get_type

_LOG = logging.getLogger(__name__)


class StandardDataFormats(Enum):
    pickle = "pickle"
    proto = "proto"
    primitive_type = "primitive_type"


class StandardSchemaFormats(Enum):
    pickled_type = "pickled_type"
    no_schema = "no_schema"


@dataclass(frozen=True)
class Schema:
    data_format: str
    schema_format: str
    schema_content: str = ''
    meta: Dict[str, str] = field(default_factory=lambda: {})


@dataclass(frozen=True)
class VersionBoundary:
    greater_than: Optional[str] = None
    less_than: Optional[str] = None


class Serializer(abc.ABC):
    HEADER_BYTES = 'serialzy'.encode('utf-8')
    HEADER_BYTES_LEN = len(HEADER_BYTES)

    def serialize(self, obj: Any, dest: BinaryIO) -> None:
        """
        :param obj: object to serialize into bytes
        :param dest: serialized obj is written into dest
        :return: None
        """

        typ = get_type(obj)
        # check that obj type is valid
        self._check_type(typ)
        # write schema header
        self._write_schema(typ, dest)
        # write serialized data
        self._serialize(obj, dest)

    @abc.abstractmethod
    def _serialize(self, obj: Any, dest: BinaryIO) -> None:
        """
        :param obj: object to serialize into bytes
        :param dest: serialized obj is written into dest
        :return: None
        """

    def deserialize(self, source: BinaryIO, typ: Optional[Type] = None) -> Any:
        """
        :param source: buffer of file with serialized data
        :param typ: type of the resulting object, fetched from the header if None
        :return: deserialized object
        """

        # read schema header
        schema_type = self._deserialize_type(source)

        # read serialized data
        return self._deserialize(source, schema_type, typ)

    @abc.abstractmethod
    def _deserialize(self, source: BinaryIO, schema_type: Type, user_type: Optional[Type] = None) -> Any:
        """
        :param source: buffer of file with serialized data
        :param schema_type: type of the resulting object retrieved from the schema header
        :param user_type: type of the resulting object provided by a user
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
    def schema(self, typ: Type) -> Schema:
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

    @abc.abstractmethod
    def requirements(self) -> Dict[str, VersionBoundary]:
        """
        :return: the requirements (libraries) which are needed to be installed to make serializer available
        """

    def _validate_schema(self, schema: Schema) -> None:
        if schema.data_format != self.data_format():
            raise TypeError(
                f"Invalid data format {schema.data_format}, expected {self.data_format()}"
            )

    def _deserialize_type(self, source: BinaryIO) -> Type:
        first_str = source.read(self.HEADER_BYTES_LEN)
        if first_str != self.HEADER_BYTES:
            raise ValueError('Invalid source format')

        header_len = int.from_bytes(source.read(8), byteorder='little', signed=False)
        schema_json = source.read(header_len).decode('utf-8')
        schema = Schema(**json.loads(schema_json))
        typ = self.resolve(schema)
        return typ

    def _write_schema(self, typ: Type, dest: BinaryIO) -> None:
        schema = self.schema(typ)
        schema_json = json.dumps(dataclasses.asdict(schema))
        schema_bytes = schema_json.encode('utf-8')
        header_len = len(schema_bytes)
        dest.write(self.HEADER_BYTES)
        dest.write(header_len.to_bytes(length=8, byteorder='little', signed=False))
        dest.write(schema_bytes)

    def _check_type(self, typ: Type) -> None:
        supported = self.supported_types()
        # mypy issue: https://github.com/python/mypy/issues/3060
        if (isinstance(supported, Type) and typ != supported) or (  # type: ignore
            not isinstance(supported, Type) and not supported(typ)):  # type: ignore
            raise TypeError(f'Invalid object type {typ} for the serializer {type(self)}')

    @staticmethod
    def _check_types_valid(schema_type: Type, user_type: Optional[Type]) -> None:
        if user_type is not None and user_type != schema_type:
            raise TypeError(f'Cannot deserialize data with schema type {schema_type} into type {user_type}')


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
    def is_registered(self, serializer: Serializer) -> bool:
        """
        :param serializer: serializer to unregister
        :return: True if serializer is registered, False otherwise
        """

    @abc.abstractmethod
    def find_serializer_by_type(self, typ: Type) -> Optional[Serializer]:
        """
        :param typ: python Type needed to serialize
        :return: corresponding serializer or None
        """

    @abc.abstractmethod
    def find_serializer_by_instance(self, obj: Any) -> Optional[Serializer]:
        """
        :param obj: instance needed to serialize
        :return: corresponding serializer or None
        """

    @abc.abstractmethod
    def find_serializer_by_data_format(self, data_format: str) -> Optional[Serializer]:
        """
        :param data_format: data format to resolve serializer
        :return: Serializer if there is a serializer for that data format, None otherwise
        """

    @abc.abstractmethod
    def reload_registry(self) -> None:
        """
        reloads all registered serializers, useful if libraries are updated
        """
