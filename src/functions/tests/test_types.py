from unittest.mock import AsyncMock, Mock, patch

from httpx import Response
from supabase_functions import (
    AsyncFunctionsClient,
    FunctionInvokeOptions,
    FunctionInvokeOptionsJson,
    FunctionInvokeOptionsNonJson,
    FunctionRegion,
    SyncFunctionsClient,
)


def test_type_exports() -> None:
    """Verify that typing symbols are properly exported from supabase_functions."""
    assert FunctionInvokeOptions is not None
    assert FunctionInvokeOptionsJson is not None
    assert FunctionInvokeOptionsNonJson is not None
    assert FunctionRegion is not None


def test_typed_dict_instantiation() -> None:
    """Verify FunctionInvokeOptions TypedDict construction."""
    options: FunctionInvokeOptions = {
        "headers": {"X-Custom-Header": "value"},
        "body": {"key": "value"},
        "method": "POST",
        "responseType": "json",
        "region": FunctionRegion.UsEast1,
    }
    assert options["method"] == "POST"
    assert options["responseType"] == "json"


async def test_async_invoke_overload_json() -> None:
    """Verify async invoke with responseType='json' returns parsed JSON without type friction."""
    client = AsyncFunctionsClient(url="https://example.com", headers={})
    mock_response = Mock(spec=Response)
    mock_response.json.return_value = {"hello": "world", "count": 42}
    mock_response.raise_for_status = Mock()
    mock_response.headers = {}

    with patch.object(client._client, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_response
        options: FunctionInvokeOptionsJson = {"responseType": "json", "body": {"q": 1}}
        result = await client.invoke("test-fn", options)

        # Result is treated as parsed JSON (Any/dict-compatible)
        assert result["hello"] == "world"
        assert result["count"] == 42


async def test_async_invoke_overload_binary_default() -> None:
    """Verify async invoke with default options returns bytes."""
    client = AsyncFunctionsClient(url="https://example.com", headers={})
    mock_response = Mock(spec=Response)
    mock_response.content = b"raw binary content"
    mock_response.raise_for_status = Mock()
    mock_response.headers = {}

    with patch.object(client._client, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_response
        result = await client.invoke("test-fn")

        # Result is treated as bytes
        assert isinstance(result, bytes)
        assert result.startswith(b"raw")


async def test_async_invoke_overload_binary_explicit() -> None:
    """Verify async invoke with responseType='text/plain' returns bytes."""
    client = AsyncFunctionsClient(url="https://example.com", headers={})
    mock_response = Mock(spec=Response)
    mock_response.content = b"text content"
    mock_response.raise_for_status = Mock()
    mock_response.headers = {}

    with patch.object(client._client, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_response
        options: FunctionInvokeOptionsNonJson = {"responseType": "text/plain"}
        result = await client.invoke("test-fn", options)

        assert isinstance(result, bytes)
        assert result == b"text content"


def test_sync_invoke_overload_json() -> None:
    """Verify sync invoke with responseType='json' returns parsed JSON."""
    client = SyncFunctionsClient(url="https://example.com", headers={})
    mock_response = Mock(spec=Response)
    mock_response.json.return_value = {"status": "ok"}
    mock_response.raise_for_status = Mock()
    mock_response.headers = {}

    with patch.object(client._client, "request", return_value=mock_response):
        options: FunctionInvokeOptionsJson = {"responseType": "json"}
        result = client.invoke("test-fn", options)

        assert result["status"] == "ok"


def test_sync_invoke_overload_binary_default() -> None:
    """Verify sync invoke with default options returns bytes."""
    client = SyncFunctionsClient(url="https://example.com", headers={})
    mock_response = Mock(spec=Response)
    mock_response.content = b"sync binary data"
    mock_response.raise_for_status = Mock()
    mock_response.headers = {}

    with patch.object(client._client, "request", return_value=mock_response):
        result = client.invoke("test-fn")

        assert isinstance(result, bytes)
        assert result == b"sync binary data"
