"""Tests that constructing a default Client/AsyncClient does not emit the
'timeout is deprecated' DeprecationWarning from sub-clients (postgrest, storage,
functions), and that custom timeout options still propagate to the underlying
httpx sessions.
"""

import warnings

from httpx import Timeout

import supabase
from supabase import AsyncClient, AsyncClientOptions, ClientOptions

# Sample project ref, URL and dummy JWT key – no network access needed.
_REF = "ooqqmozurnggtljmjkii"
_URL = f"https://{_REF}.supabase.co"
_KEY = "xxxxxxxxxxxxxx.xxxxxxxxxxxxxxx.xxxxxxxxxxxxxxx"

_TIMEOUT_WARNING_MSG = "The 'timeout' parameter is deprecated"
_VERIFY_WARNING_MSG = "The 'verify' parameter is deprecated"
_PROXY_WARNING_MSG = "The 'proxy' parameter is deprecated"


def _collect_timeout_deprecations(caught: list) -> list:
    return [
        w
        for w in caught
        if issubclass(w.category, DeprecationWarning)
        and (
            _TIMEOUT_WARNING_MSG in str(w.message)
            or _VERIFY_WARNING_MSG in str(w.message)
            or _PROXY_WARNING_MSG in str(w.message)
        )
    ]


class TestNoDeprecationWarningSync:
    def test_no_timeout_deprecation_warning_on_default_client(self) -> None:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            client = supabase.Client(_URL, _KEY)
            _ = client.postgrest
            _ = client.storage
            _ = client.functions

        timeout_warnings = _collect_timeout_deprecations(caught)
        assert timeout_warnings == [], (
            f"Unexpected deprecation warnings: {[str(w.message) for w in timeout_warnings]}"
        )

    def test_postgrest_client_timeout_propagates(self) -> None:
        options = ClientOptions(postgrest_client_timeout=5.0)
        client = supabase.Client(_URL, _KEY, options=options)
        assert client.postgrest.session.timeout == Timeout(5.0)

    def test_storage_client_timeout_propagates(self) -> None:
        options = ClientOptions(storage_client_timeout=7)
        client = supabase.Client(_URL, _KEY, options=options)
        assert client.storage.session.timeout == Timeout(7)

    def test_function_client_timeout_propagates(self) -> None:
        options = ClientOptions(function_client_timeout=3)
        client = supabase.Client(_URL, _KEY, options=options)
        assert client.functions._client.timeout == Timeout(3)


class TestNoDeprecationWarningAsync:
    async def test_no_timeout_deprecation_warning_on_default_async_client(
        self,
    ) -> None:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            client = AsyncClient(_URL, _KEY)
            _ = client.postgrest
            _ = client.storage
            _ = client.functions

        timeout_warnings = _collect_timeout_deprecations(caught)
        assert timeout_warnings == [], (
            f"Unexpected deprecation warnings: {[str(w.message) for w in timeout_warnings]}"
        )

    async def test_postgrest_client_timeout_propagates_async(self) -> None:
        options = AsyncClientOptions(postgrest_client_timeout=5.0)
        client = AsyncClient(_URL, _KEY, options=options)
        assert client.postgrest.session.timeout == Timeout(5.0)

    async def test_storage_client_timeout_propagates_async(self) -> None:
        options = AsyncClientOptions(storage_client_timeout=7)
        client = AsyncClient(_URL, _KEY, options=options)
        assert client.storage.session.timeout == Timeout(7)

    async def test_function_client_timeout_propagates_async(self) -> None:
        options = AsyncClientOptions(function_client_timeout=3)
        client = AsyncClient(_URL, _KEY, options=options)
        assert client.functions._client.timeout == Timeout(3)
