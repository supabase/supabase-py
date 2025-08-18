from __future__ import annotations
from typing import Iterable, TypeVar, Union

T = TypeVar("T")

def maybe_single(value: Union[T, Iterable[T], None]) -> Union[T, list[T], None]:
    """
    If value is a 1-length list/tuple, unwrap to the single item.
    If it's a longer tuple, return a list. If it's None or a scalar, return as-is.
    """
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        if len(value) == 1:
            return value[0]
        # normalize tuples to list for consistency
        return list(value) if isinstance(value, tuple) else value
    return value
