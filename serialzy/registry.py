import inspect
import logging
import sys
from collections import defaultdict
from types import ModuleType
from typing import Dict, List, Optional, Type, cast, Iterable

import serialzy.serializers
from serialzy.api import Serializer, SerializerRegistry
from serialzy.cloudpickle import CloudpickleSerializer
from serialzy.utils import load_all_modules_from

_LOG = logging.getLogger(__name__)


class DefaultSerializerRegistry(SerializerRegistry):
    def __init__(self):
        self._default_priority_stable = sys.maxsize - 10
        self._default_priority_unstable = sys.maxsize - 5

        self._type_registry: Dict[Type, Serializer] = {}
        self._data_formats_serializer_registry: Dict[str, List[Serializer]] = defaultdict(list)

        self._serializer_priorities: Dict[Type[Serializer], int] = {}
        self._serializer_registry: Dict[Type[Serializer], Serializer] = {}

        load_all_modules_from(serialzy.serializers)
        for serializer in self._fetch_serializers_from(serialzy.serializers):
            if serializer.stable():
                self.register_serializer(serializer, self._default_priority_stable)
            else:
                self.register_serializer(serializer, self._default_priority_unstable)
        # cloudpickle has the least priority
        self.register_serializer(CloudpickleSerializer(), sys.maxsize - 1)

    def register_serializer(self, serializer: Serializer, priority: Optional[int] = None) -> None:
        serializer_type = type(serializer)
        if not serializer.available():
            _LOG.debug(f"Serializer {serializer_type} cannot be registered")
            return

        if serializer_type in self._serializer_registry:
            raise ValueError(f"Serializer {serializer_type} has been already registered")

        if isinstance(serializer.supported_types(),
                      Type) and serializer.supported_types() in self._type_registry:  # type: ignore
            raise ValueError(
                f"Serializer for type {serializer.supported_types()} has been already registered"
            )

        if priority is None:
            if serializer.stable():
                priority = self._default_priority_stable
            else:
                priority = self._default_priority_unstable

        self._serializer_priorities[serializer_type] = priority
        self._serializer_registry[serializer_type] = serializer

        self._data_formats_serializer_registry[serializer.data_format()].append(serializer)
        # mypy issue: https://github.com/python/mypy/issues/3060
        if isinstance(serializer.supported_types(), Type):  # type: ignore
            self._type_registry[cast(Type, serializer.supported_types())] = serializer

    def unregister_serializer(self, serializer: Serializer):
        serializer_type = type(serializer)
        if serializer_type in self._serializer_registry:
            # mypy issue: https://github.com/python/mypy/issues/3060
            if isinstance(serializer.supported_types(), Type):  # type: ignore
                del self._type_registry[cast(Type, serializer.supported_types())]
            self._data_formats_serializer_registry[serializer.data_format()].remove(serializer)

            del self._serializer_priorities[serializer_type]
            del self._serializer_registry[serializer_type]

    def find_serializer_by_type(self, typ: Type) -> Serializer:
        filter_ser: Optional[Serializer] = None
        filter_ser_priority = sys.maxsize
        for serializer_type, serializer in self._serializer_registry.items():
            if (
                    # mypy issue: https://github.com/python/mypy/issues/3060
                    not isinstance(serializer.supported_types(), Type)  # type: ignore
                    and serializer.supported_types()(typ)
                    and self._serializer_priorities[serializer_type] < filter_ser_priority
            ):
                filter_ser_priority = self._serializer_priorities[serializer_type]
                filter_ser = serializer

        obj_type_ser: Optional[Serializer] = (
            self._type_registry[typ] if typ in self._type_registry else None
        )
        obj_type_ser_priority = (
            sys.maxsize
            if obj_type_ser is None
            else self._serializer_priorities[type(obj_type_ser)]
        )

        if obj_type_ser is not None:
            return (
                cast(Serializer, filter_ser)
                if filter_ser_priority < obj_type_ser_priority
                else obj_type_ser
            )
        return cast(Serializer, filter_ser)

    def find_serializer_by_data_format(self, data_format: str) -> Optional[Serializer]:
        serializer: Optional[Serializer] = None
        serializer_priority = sys.maxsize
        for ser in self._data_formats_serializer_registry[data_format]:
            ser_type = type(ser)
            if self._serializer_priorities[ser_type] < serializer_priority:
                serializer = ser
                serializer_priority = self._serializer_priorities[ser_type]
        return serializer

    def _fetch_serializers_from(self, module: ModuleType) -> Iterable[Serializer]:
        stable_serializer_modules = dir(module)
        for module_attr in stable_serializer_modules:
            module_value = getattr(module, module_attr)
            if isinstance(module_value, ModuleType):
                stable_serializers = dir(module_value)
                for class_attr in stable_serializers:
                    class_value = getattr(module_value, class_attr)
                    if inspect.isclass(class_value) and not inspect.isabstract(class_value) and issubclass(class_value,
                                                                                                           Serializer):
                        sig = inspect.signature(class_value)
                        if len(sig.parameters) == 0:
                            instance = class_value()
                        elif len(sig.parameters) == 1 and issubclass(list(sig.parameters.values())[0].annotation,
                                                                     SerializerRegistry):
                            # noinspection PyArgumentList
                            instance = class_value(self)  # type: ignore
                        else:
                            raise ValueError(
                                f'Serializer {class_value.__name__} has unexpected arguments in __init__: '
                                f'only empty arguments or SerializerRegistry are allowed')

                        yield instance
