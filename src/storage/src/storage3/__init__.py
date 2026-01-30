from __future__ import annotations

from typing import Literal, Union, overload

from storage3.client import AsyncStorageClient, SyncStorageClient
from storage3.version import __version__

__all__ = [
    "create_client",
    "__version__",
    "AsyncStorageClient",
    "SyncStorageClient",
]


@overload
def create_client(
    url: str, headers: dict[str, str], *, is_async: Literal[True]
) -> AsyncStorageClient: ...


@overload
def create_client(
    url: str, headers: dict[str, str], *, is_async: Literal[False]
) -> SyncStorageClient: ...


def create_client(
    url: str, headers: dict[str, str], *, is_async: bool
) -> Union[AsyncStorageClient, SyncStorageClient]:
    if is_async:
        return AsyncStorageClient(url, headers)
    else:
        return SyncStorageClient(url, headers)
