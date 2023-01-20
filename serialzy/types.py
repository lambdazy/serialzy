from typing import Any, Type, List, Tuple


class EmptyListContent:
    pass


def get_type(obj: Any) -> Type:
    original_type = type(obj)
    if original_type == list and len(obj) > 0:
        return List[get_type(obj[0])]  # type: ignore  # suppose here that all elements have the same type
    elif original_type == tuple and 0 < len(obj) <= 20:  # suppose that a human cannot make tuple with more than 20 args
        return Tuple[tuple(get_type(x) for x in obj)]  # type: ignore
    elif original_type == tuple and len(obj) > 0 and all(isinstance(x, type(obj[0])) for x in obj):
        return Tuple[get_type(obj[0]), ...]  # type: ignore
    elif original_type == list and len(obj) == 0:
        return List[EmptyListContent]  # type: ignore
    elif original_type == tuple and len(obj) == 0:
        return Tuple[EmptyListContent]  # type: ignore
    else:
        return original_type
