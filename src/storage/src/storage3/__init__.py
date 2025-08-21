from __future__ import annotations

from typing import Literal, Union, overload

from storage3._async import AsyncStorageClient
from storage3._async.bucket import AsyncStorageBucketAPI
from storage3._async.file_api import AsyncBucket
from storage3._sync import SyncStorageClient
from storage3._sync.bucket import SyncStorageBucketAPI
from storage3._sync.file_api import SyncBucket
from storage3.constants import DEFAULT_TIMEOUT
from storage3.version import __version__

__all__ = [
    "create_client",
    "__version__",
    "AsyncStorageClient",
    "AsyncBucket",
    "AsyncStorageBucketAPI",
    "SyncStorageClient",
    "SyncBucket",
    "SyncStorageBucketAPI",
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
    url: str, headers: dict[str, str], *, is_async: bool, timeout: int = DEFAULT_TIMEOUT
) -> Union[AsyncStorageClient, SyncStorageClient]:
    if is_async:
        return AsyncStorageClient(url, headers, timeout)
    else:
        return SyncStorageClient(url, headers, timeout)
