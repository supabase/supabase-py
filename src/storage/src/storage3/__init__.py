from __future__ import annotations

from typing import Literal, overload

from storage3._async import AsyncStorageClient
from storage3._async.bucket import AsyncStorageBucketAPI
from storage3._async.file_api import AsyncBucket
from storage3._sync import SyncStorageClient
from storage3._sync.bucket import SyncStorageBucketAPI
from storage3._sync.file_api import SyncBucket
from storage3.constants import DEFAULT_TIMEOUT as DEFAULT_TIMEOUT
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
    url: str,
    headers: dict[str, str],
    *,
    is_async: Literal[True],
    timeout: int | None = None,
) -> AsyncStorageClient: ...


@overload
def create_client(
    url: str,
    headers: dict[str, str],
    *,
    is_async: Literal[False],
    timeout: int | None = None,
) -> SyncStorageClient: ...


def create_client(
    url: str,
    headers: dict[str, str],
    *,
    is_async: bool,
    timeout: int | None = None,
) -> AsyncStorageClient | SyncStorageClient:
    client_class = AsyncStorageClient if is_async else SyncStorageClient
    if timeout is None:
        return client_class(url, headers)
    return client_class(url, headers, timeout)
