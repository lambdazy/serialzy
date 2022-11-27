import abc
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, BinaryIO, Callable, Dict, Optional, Type, TypeVar, Union

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
    @abc.abstractmethod
    def serialize(self, obj: Any, dest: BinaryIO) -> None:
        """
        :param obj: object to serialize into bytes
        :param dest: serialized obj is written into dest
        :return: None
        """

    @abc.abstractmethod
    def deserialize(self, source: BinaryIO, typ: Type[T]) -> T:
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


class SerializerRegistry(abc.ABC):
    @abc.abstractmethod
    def register_serializer(
            self, name: str, serializer: Serializer, priority: Optional[int] = None
    ) -> None:
        """
        :param name: unique serializer's name
        :param serializer: serializer to register
        :param priority: number that indicates serializer's priority: 0 - max priority
        :return: None
        """

    @abc.abstractmethod
    def unregister_serializer(self, name: str) -> None:
        """
        :param name: name of the serializer to unregister
        :return:
        """

    @abc.abstractmethod
    def find_serializer_by_type(
            self, typ: Type
    ) -> Serializer:  # we assume that default serializer always can be found
        """
        :param typ: python Type needed to serialize
        :return: corresponding serializer
        """

    @abc.abstractmethod
    def find_serializer_by_name(self, serializer_name: str) -> Optional[Serializer]:
        """
        :param serializer_name: target name
        :return: Serializer registered with serializer_name or None
        """

    @abc.abstractmethod
    def resolve_name(self, serializer: Serializer) -> Optional[str]:
        """
        :param serializer: serializer to resolve name
        :return: name if the serializer is registered, None otherwise
        """

    @abc.abstractmethod
    def find_serializer_by_data_format(self, data_format: str) -> Optional[Serializer]:
        """
        :param data_format: data format to resolve serializer
        :return: Serializer if there is a serializer for that data format, None otherwise
        """
