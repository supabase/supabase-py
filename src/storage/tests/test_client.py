import re
from typing import Any, Dict, Mapping
from unittest.mock import AsyncMock, Mock, patch

import pytest
try:
    from httpx2 import AsyncClient, Client, Headers, Request, Response, Timeout
except ImportError:
    from httpx import AsyncClient, Client, Headers, Request, Response, Timeout
from storage3 import AsyncStorageClient, SyncStorageClient
from storage3._async.file_api import AsyncBucketProxy
from storage3._sync.file_api import SyncBucketProxy
from storage3.constants import DEFAULT_TIMEOUT
from storage3.exceptions import StorageApiError
from yarl import URL


@pytest.fixture
def valid_url() -> str:
    return "https://example.com/storage/v1"


@pytest.fixture
def valid_headers() -> Dict[str, str]:
    return {"Authorization": "Bearer test_token", "apikey": "test_api_key"}


_X_CLIENT_INFO_PATTERN = re.compile(
    r"^supabase-py/storage3 v[\d.]+; platform=.+; platform-version=.+; runtime=python; runtime-version=\S+$"
)


def test_async_x_client_info_structured_format(valid_url, valid_headers) -> None:
    client = AsyncStorageClient(url=valid_url, headers=valid_headers)
    x_client_info = client._client.headers.get("X-Client-Info")
    assert x_client_info is not None
    assert _X_CLIENT_INFO_PATTERN.match(x_client_info), (
        f"X-Client-Info format is wrong: {x_client_info}"
    )


def test_sync_x_client_info_structured_format(valid_url, valid_headers) -> None:
    client = SyncStorageClient(url=valid_url, headers=valid_headers)
    x_client_info = client._client.headers.get("X-Client-Info")
    assert x_client_info is not None
    assert _X_CLIENT_INFO_PATTERN.match(x_client_info), (
        f"X-Client-Info format is wrong: {x_client_info}"
    )


def test_create_async_client(valid_url, valid_headers) -> None:
    client = AsyncStorageClient(url=valid_url, headers=valid_headers)

    assert isinstance(client, AsyncStorageClient)
    assert all(
        client._client.headers[key] == value for key, value in valid_headers.items()
    )
    assert client._client.timeout == Timeout(DEFAULT_TIMEOUT)


def test_create_sync_client(valid_url, valid_headers) -> None:
    client = SyncStorageClient(url=valid_url, headers=valid_headers)

    assert isinstance(client, SyncStorageClient)
    assert all(
        client._client.headers[key] == value for key, value in valid_headers.items()
    )
    assert client._client.timeout == Timeout(DEFAULT_TIMEOUT)


def test_async_storage_client(valid_url, valid_headers) -> None:
    headers = {"x-user-agent": "my-app/0.0.1"}
    http_client = AsyncClient(headers=headers)
    client = AsyncStorageClient(
        url=valid_url, headers=valid_headers, http_client=http_client
    )

    assert isinstance(client, AsyncStorageClient)
    assert all(client._headers[key] == value for key, value in valid_headers.items())
    assert client._client.headers.get("x-user-agent") == "my-app/0.0.1"
    assert client._client.timeout == Timeout(5.0)


def test_sync_storage_client(valid_url, valid_headers) -> None:
    headers = {"x-user-agent": "my-app/0.0.1"}
    http_client = Client(headers=headers)
    client = SyncStorageClient(
        url=valid_url, headers=valid_headers, http_client=http_client
    )

    assert isinstance(client, SyncStorageClient)
    assert all(client._headers[key] == value for key, value in valid_headers.items())
    assert client._client.headers.get("x-user-agent") == "my-app/0.0.1"
    assert client._client.timeout == Timeout(5.0)


def test_async_storage_client_with_httpx(valid_url, valid_headers) -> None:
    client = AsyncStorageClient(url=valid_url, headers=valid_headers)

    assert isinstance(client, AsyncStorageClient)
    assert all(
        client._client.headers[key] == value for key, value in valid_headers.items()
    )
    assert client._client.timeout == Timeout(DEFAULT_TIMEOUT)


def test_sync_storage_client_with_httpx(valid_url, valid_headers) -> None:
    client = SyncStorageClient(url=valid_url, headers=valid_headers)

    assert isinstance(client, SyncStorageClient)
    assert all(
        client._client.headers[key] == value for key, value in valid_headers.items()
    )
    assert client._client.timeout == Timeout(DEFAULT_TIMEOUT)


def test_custom_timeout(valid_url, valid_headers) -> None:
    custom_timeout = 30

    async_client = AsyncStorageClient(
        url=valid_url, headers=valid_headers, timeout=custom_timeout
    )
    assert async_client._client.timeout == Timeout(custom_timeout)

    sync_client = SyncStorageClient(
        url=valid_url, headers=valid_headers, timeout=custom_timeout
    )
    assert sync_client._client.timeout == Timeout(custom_timeout)


def _mock_upload_response() -> Mock:
    response = Mock()
    response.json.return_value = {"Key": "bucket/file.txt", "Id": "id"}
    return response


def _async_bucket_proxy() -> AsyncBucketProxy:
    client = AsyncMock()
    client.headers = {}
    return AsyncBucketProxy(
        "bucket", URL("https://example.com/storage/v1/"), Headers(), client
    )


def _sync_bucket_proxy() -> SyncBucketProxy:
    client = Mock()
    client.headers = {}
    return SyncBucketProxy(
        "bucket", URL("https://example.com/storage/v1/"), Headers(), client
    )


def _request_kwargs(request: Mock) -> Mapping[str, Any]:
    call = request.call_args
    assert call is not None
    return call.kwargs


def _assert_multipart_cache_control(request: Mock, expected: str) -> None:
    kwargs = _request_kwargs(request)
    assert "cache-control" not in kwargs["headers"]
    assert kwargs["data"]["cacheControl"] == expected


@pytest.mark.asyncio
async def test_async_upload_sends_default_cache_control_as_form_data() -> None:
    proxy = _async_bucket_proxy()
    with patch.object(proxy, "_request", new_callable=AsyncMock) as request:
        request.return_value = _mock_upload_response()
        await proxy.upload("file.txt", b"hello")

    _assert_multipart_cache_control(request, "3600")


@pytest.mark.asyncio
async def test_async_upload_sends_custom_cache_control_as_form_data() -> None:
    proxy = _async_bucket_proxy()
    with patch.object(proxy, "_request", new_callable=AsyncMock) as request:
        request.return_value = _mock_upload_response()
        await proxy.upload(
            "file.txt",
            b"hello",
            {
                "cache-control": "86400",
                "headers": {"x-custom-header": "custom-value"},
            },
        )

    _assert_multipart_cache_control(request, "86400")
    assert _request_kwargs(request)["headers"]["x-custom-header"] == "custom-value"


def test_sync_upload_sends_default_cache_control_as_form_data() -> None:
    proxy = _sync_bucket_proxy()
    with patch.object(proxy, "_request") as request:
        request.return_value = _mock_upload_response()
        proxy.upload("file.txt", b"hello")

    _assert_multipart_cache_control(request, "3600")


def test_sync_upload_sends_custom_cache_control_as_form_data() -> None:
    proxy = _sync_bucket_proxy()
    with patch.object(proxy, "_request") as request:
        request.return_value = _mock_upload_response()
        proxy.upload(
            "file.txt",
            b"hello",
            {
                "cache-control": "86400",
                "headers": {"x-custom-header": "custom-value"},
            },
        )

    _assert_multipart_cache_control(request, "86400")
    assert _request_kwargs(request)["headers"]["x-custom-header"] == "custom-value"


@pytest.mark.asyncio
async def test_async_update_sends_cache_control_as_form_data() -> None:
    proxy = _async_bucket_proxy()
    with patch.object(proxy, "_request", new_callable=AsyncMock) as request:
        request.return_value = _mock_upload_response()
        await proxy.update("file.txt", b"hello", {"cache-control": "7200"})

    _assert_multipart_cache_control(request, "7200")
    assert "x-upsert" not in _request_kwargs(request)["headers"]


def test_sync_update_sends_cache_control_as_form_data() -> None:
    proxy = _sync_bucket_proxy()
    with patch.object(proxy, "_request") as request:
        request.return_value = _mock_upload_response()
        proxy.update("file.txt", b"hello", {"cache-control": "7200"})

    _assert_multipart_cache_control(request, "7200")
    assert "x-upsert" not in _request_kwargs(request)["headers"]


@pytest.mark.asyncio
async def test_async_signed_upload_sends_default_cache_control() -> None:
    proxy = _async_bucket_proxy()
    with patch.object(proxy, "_request", new_callable=AsyncMock) as request:
        request.return_value = _mock_upload_response()
        await proxy.upload_to_signed_url("file.txt", "token", b"hello")

    _assert_multipart_cache_control(request, "3600")


def test_sync_signed_upload_sends_default_cache_control() -> None:
    proxy = _sync_bucket_proxy()
    with patch.object(proxy, "_request") as request:
        request.return_value = _mock_upload_response()
        proxy.upload_to_signed_url("file.txt", "token", b"hello")

    _assert_multipart_cache_control(request, "3600")


@pytest.mark.asyncio
async def test_async_upload_to_signed_url_forwards_all_file_options() -> None:
    proxy = _async_bucket_proxy()
    with patch.object(proxy, "_request", new_callable=AsyncMock) as request:
        request.return_value = _mock_upload_response()
        await proxy.upload_to_signed_url(
            "file.txt",
            "token",
            b"hello",
            {
                "cache-control": "86400",
                "content-type": "text/custom",
                "metadata": {"owner": "alice"},
                "headers": {"x-custom-header": "custom-value"},
            },
        )

    kwargs = _request_kwargs(request)
    _assert_multipart_cache_control(request, "86400")
    assert kwargs["data"]["metadata"] == '{"owner": "alice"}'
    assert kwargs["headers"]["x-custom-header"] == "custom-value"
    assert "metadata" not in kwargs["headers"]
    assert "headers" not in kwargs["headers"]
    assert "x-metadata" not in kwargs["headers"]
    assert kwargs["files"]["file"][2] == "text/custom"


def test_sync_upload_to_signed_url_forwards_all_file_options() -> None:
    proxy = _sync_bucket_proxy()
    with patch.object(proxy, "_request") as request:
        request.return_value = _mock_upload_response()
        proxy.upload_to_signed_url(
            "file.txt",
            "token",
            b"hello",
            {
                "cache-control": "86400",
                "content-type": "text/custom",
                "metadata": {"owner": "alice"},
                "headers": {"x-custom-header": "custom-value"},
            },
        )

    kwargs = _request_kwargs(request)
    _assert_multipart_cache_control(request, "86400")
    assert kwargs["data"]["metadata"] == '{"owner": "alice"}'
    assert kwargs["headers"]["x-custom-header"] == "custom-value"
    assert "metadata" not in kwargs["headers"]
    assert "headers" not in kwargs["headers"]
    assert "x-metadata" not in kwargs["headers"]
    assert kwargs["files"]["file"][2] == "text/custom"


def test_sync_bucket_proxy_request_missing_error_keys() -> None:
    proxy = _sync_bucket_proxy()
    mock_response = Response(
        status_code=413,
        json={"code": "PayloadTooLarge"},
        request=Request("POST", "https://example.com"),
    )
    with patch.object(proxy._client, "request", return_value=mock_response):
        with pytest.raises(StorageApiError) as exc_info:
            proxy._request("POST", ["object", "file.txt"])

    err = exc_info.value
    assert "PayloadTooLarge" in err.message
    assert err.code == "InternalError"
    assert err.status == 413


@pytest.mark.asyncio
async def test_async_bucket_proxy_request_missing_error_keys() -> None:
    proxy = _async_bucket_proxy()
    mock_response = Response(
        status_code=413,
        json={"code": "PayloadTooLarge"},
        request=Request("POST", "https://example.com"),
    )
    with patch.object(
        proxy._client, "request", new_callable=AsyncMock, return_value=mock_response
    ):
        with pytest.raises(StorageApiError) as exc_info:
            await proxy._request("POST", ["object", "file.txt"])

    err = exc_info.value
    assert "PayloadTooLarge" in err.message
    assert err.code == "InternalError"
    assert err.status == 413


def test_sync_bucket_proxy_request_non_json_error() -> None:
    proxy = _sync_bucket_proxy()
    mock_response = Response(
        status_code=504,
        text="<html>504 Gateway Timeout</html>",
        request=Request("POST", "https://example.com"),
    )
    with patch.object(proxy._client, "request", return_value=mock_response):
        with pytest.raises(StorageApiError) as exc_info:
            proxy._request("POST", ["object", "file.txt"])

    err = exc_info.value
    assert "504 Gateway Timeout" in err.message
    assert err.code == "InternalError"
    assert err.status == 504


@pytest.mark.asyncio
async def test_async_bucket_proxy_request_non_json_error() -> None:
    proxy = _async_bucket_proxy()
    mock_response = Response(
        status_code=504,
        text="<html>504 Gateway Timeout</html>",
        request=Request("POST", "https://example.com"),
    )
    with patch.object(
        proxy._client, "request", new_callable=AsyncMock, return_value=mock_response
    ):
        with pytest.raises(StorageApiError) as exc_info:
            await proxy._request("POST", ["object", "file.txt"])

    err = exc_info.value
    assert "504 Gateway Timeout" in err.message
    assert err.code == "InternalError"
    assert err.status == 504


def test_sync_bucket_proxy_exists_false_on_headless_error() -> None:
    proxy = _sync_bucket_proxy()
    mock_response = Response(
        status_code=400, request=Request("HEAD", "https://example.com")
    )
    with patch.object(proxy._client, "request", return_value=mock_response):
        assert proxy.exists("missing.txt") is False


def test_sync_bucket_proxy_exists_reraises_unexpected_status() -> None:
    proxy = _sync_bucket_proxy()
    mock_response = Response(
        status_code=401, request=Request("HEAD", "https://example.com")
    )
    with patch.object(proxy._client, "request", return_value=mock_response):
        with pytest.raises(StorageApiError):
            proxy.exists("missing.txt")


@pytest.mark.asyncio
async def test_async_bucket_proxy_exists_false_on_headless_error() -> None:
    proxy = _async_bucket_proxy()
    mock_response = Response(
        status_code=400, request=Request("HEAD", "https://example.com")
    )
    with patch.object(
        proxy._client, "request", new_callable=AsyncMock, return_value=mock_response
    ):
        assert await proxy.exists("missing.txt") is False
