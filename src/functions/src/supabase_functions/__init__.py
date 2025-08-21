from __future__ import annotations

from typing import Literal, Union, overload

from ._async.functions_client import AsyncFunctionsClient
from ._sync.functions_client import SyncFunctionsClient
from .utils import FunctionRegion

__all__ = [
    "create_client",
    "FunctionRegion",
    "AsyncFunctionsClient",
    "SyncFunctionsClient",
]


@overload
def create_client(
    url: str, headers: dict[str, str], *, is_async: Literal[True], verify: bool
) -> AsyncFunctionsClient: ...


@overload
def create_client(
    url: str, headers: dict[str, str], *, is_async: Literal[False], verify: bool
) -> SyncFunctionsClient: ...


def create_client(
    url: str,
    headers: dict[str, str],
    *,
    is_async: bool,
    verify: bool = True,
) -> Union[AsyncFunctionsClient, SyncFunctionsClient]:
    if is_async:
        return AsyncFunctionsClient(url, headers, verify)
    else:
        return SyncFunctionsClient(url, headers, verify)
