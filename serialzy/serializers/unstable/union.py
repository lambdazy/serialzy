from typing import Union, Type, Callable, Tuple, Any
from typing_extensions import get_origin, get_args
from serialzy.serializers.union_base import UnionSerializerBase


class UnionSerializerUnstable(UnionSerializerBase):
    def supported_types(self) -> Union[Type, Callable[[Type], bool]]:
        return lambda t: get_origin(t) is not None and self.__check_args(get_args(t))

    def stable(self) -> bool:
        return False

    def __check_args(self, args: Tuple[Any, ...]) -> bool:
        for arg in args:
            serializer = self._registry.find_serializer_by_type(arg)
            if serializer is None:
                return False
        return True
