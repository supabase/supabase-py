import warnings

import pytest
from storage3 import AsyncStorageClient, SyncStorageClient, create_client
from storage3.constants import DEFAULT_TIMEOUT

URL = "https://example.supabase.co/storage/v1/"


async def test_async_create_client_does_not_warn_by_default() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        client = create_client(URL, {}, is_async=True)
    try:
        assert isinstance(client, AsyncStorageClient)
        assert client.timeout == DEFAULT_TIMEOUT
    finally:
        await client.session.aclose()


def test_sync_create_client_does_not_warn_by_default() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        client = create_client(URL, {}, is_async=False)
    try:
        assert isinstance(client, SyncStorageClient)
        assert client.timeout == DEFAULT_TIMEOUT
    finally:
        client.session.close()


async def test_async_create_client_applies_explicit_timeout() -> None:
    with pytest.warns(DeprecationWarning, match="timeout"):
        client = create_client(URL, {}, is_async=True, timeout=42)
    try:
        assert client.timeout == 42
        assert client.session.timeout.read == 42
    finally:
        await client.session.aclose()


def test_sync_create_client_applies_explicit_timeout() -> None:
    with pytest.warns(DeprecationWarning, match="timeout"):
        client = create_client(URL, {}, is_async=False, timeout=42)
    try:
        assert client.timeout == 42
        assert client.session.timeout.read == 42
    finally:
        client.session.close()
