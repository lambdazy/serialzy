import inspect
import logging
import sys
from collections import OrderedDict, defaultdict
from types import ModuleType
from typing import Dict, List, Optional, Type, cast

import serialzy.serializers.stable
import serialzy.serializers.unstable
from serialzy.api import Serializer, SerializerRegistry
from serialzy.utils import load_all_modules_from

_LOG = logging.getLogger(__name__)


class DefaultSerializerRegistry(SerializerRegistry):
    def __init__(self):
        self._default_priority = sys.maxsize - 10
        self._default_priority_unstable = sys.maxsize - 1
        self._type_registry: Dict[Type, Serializer] = {}
        self._type_name_registry: Dict[Type, str] = {}
        self._name_registry: Dict[str, Serializer] = OrderedDict()
        self._data_formats_name_registry: Dict[str, List[str]] = defaultdict(list)
        self._serializer_priorities: Dict[str, int] = {}

        load_all_modules_from(serialzy.serializers.stable)
        load_all_modules_from(serialzy.serializers.unstable)

        self._register_serializers_from(serialzy.serializers.stable, self._default_priority)
        self._register_serializers_from(serialzy.serializers.unstable, self._default_priority_unstable)

    def register_serializer(
            self, name: str, serializer: Serializer, priority: Optional[int] = None
    ) -> None:
        if not serializer.available():
            _LOG.debug(f"Serializer {name} cannot be registered")
            return

        if name in self._serializer_priorities:
            raise ValueError(f"Serializer {name} has been already registered")

        if isinstance(serializer.supported_types(),
                      Type) and serializer.supported_types() in self._type_registry:  # type: ignore
            raise ValueError(
                f"Serializer for type {serializer.supported_types()} has been already registered"
            )

        priority = self._default_priority if priority is None else priority
        self._serializer_priorities[name] = priority
        self._name_registry[name] = serializer
        self._data_formats_name_registry[serializer.data_format()].append(name)
        # mypy issue: https://github.com/python/mypy/issues/3060
        if isinstance(serializer.supported_types(), Type):  # type: ignore
            self._type_registry[cast(Type, serializer.supported_types())] = serializer
            self._type_name_registry[cast(Type, serializer.supported_types())] = name

    def unregister_serializer(self, name: str):
        if name in self._serializer_priorities:
            serializer = self._name_registry[name]
            # mypy issue: https://github.com/python/mypy/issues/3060
            if isinstance(serializer.supported_types(), Type):  # type: ignore
                del self._type_registry[cast(Type, serializer.supported_types())]
                del self._type_name_registry[cast(Type, serializer.supported_types())]
                self._data_formats_name_registry[serializer.data_format()].remove(name)
            del self._serializer_priorities[name]
            del self._name_registry[name]

    def find_serializer_by_type(self, typ: Type) -> Serializer:
        filter_ser: Optional[Serializer] = None
        filter_ser_priority = sys.maxsize
        for name, serializer in self._name_registry.items():
            if (
                    # mypy issue: https://github.com/python/mypy/issues/3060
                    not isinstance(serializer.supported_types(), Type)  # type: ignore
                    and serializer.supported_types()(typ)
                    and self._serializer_priorities[name] < filter_ser_priority
            ):
                filter_ser_priority = self._serializer_priorities[name]
                filter_ser = serializer

        obj_type_ser: Optional[Serializer] = (
            self._type_registry[typ] if typ in self._type_registry else None
        )
        obj_type_ser_priority = (
            sys.maxsize
            if obj_type_ser is None
            else self._serializer_priorities[self._type_name_registry[typ]]
        )

        if obj_type_ser is not None:
            return (
                cast(Serializer, filter_ser)
                if filter_ser_priority < obj_type_ser_priority
                else obj_type_ser
            )
        return cast(Serializer, filter_ser)

    def find_serializer_by_name(self, serializer_name: str) -> Optional[Serializer]:
        if serializer_name in self._name_registry:
            return self._name_registry[serializer_name]
        return None

    def resolve_name(self, serializer: Serializer) -> Optional[str]:
        for name, s in self._name_registry.items():
            if serializer == s:
                return name
        return None

    def find_serializer_by_data_format(self, data_format: str) -> Optional[Serializer]:
        serializer: Optional[Serializer] = None
        serializer_priority = sys.maxsize
        for name in self._data_formats_name_registry[data_format]:
            if self._serializer_priorities[name] < serializer_priority:
                serializer = self._name_registry[name]
                serializer_priority = self._serializer_priorities[name]
        return serializer

    def _register_serializers_from(self, module: ModuleType, priority: int) -> None:
        stable_serializer_modules = dir(module)
        for module_attr in stable_serializer_modules:
            module_value = getattr(module, module_attr)
            if isinstance(module_value, ModuleType):
                stable_serializers = dir(module_value)
                for class_attr in stable_serializers:
                    class_value = getattr(module_value, class_attr)
                    if inspect.isclass(class_value) and not inspect.isabstract(class_value) and issubclass(class_value,
                                                                                                           Serializer):
                        self.register_serializer("Serialzy" + class_value.__name__, class_value(), priority)
