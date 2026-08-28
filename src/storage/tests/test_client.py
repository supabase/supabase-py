import re
from typing import Any, Dict, Mapping
from unittest.mock import AsyncMock, Mock, patch

import pytest
from httpx import AsyncClient, Client, Headers, Timeout
from storage3 import AsyncStorageClient, SyncStorageClient
from storage3._async.file_api import AsyncBucketProxy
from storage3._sync.file_api import SyncBucketProxy
from storage3.constants import DEFAULT_TIMEOUT
from storage3.types import CreateSignedUploadUrlOptions
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


def _mock_signed_upload_url_response(path: str) -> Mock:
    """A Storage API response for a single signed upload URL."""
    response = Mock()
    response.json.return_value = {
        "url": f"/object/upload/sign/bucket/{path}?token=token-{path}"
    }
    return response


def test_sync_create_signed_upload_urls_signs_each_path() -> None:
    proxy = _sync_bucket_proxy()
    paths = ["folder/image.png", "nested/dir/photo.jpg", "solo.txt"]

    def fake_request(*args: Any, **kwargs: Any) -> Mock:
        return _mock_signed_upload_url_response("/".join(args[1][4:]))

    with patch.object(proxy, "_request", side_effect=fake_request) as request:
        results = proxy.create_signed_upload_urls(paths)

    assert request.call_count == len(paths)
    assert len(results) == len(paths)
    for path, result in zip(paths, results):
        assert result["path"] == path
        assert result["token"] == f"token-{path}"
        assert result["signed_url"] == (
            f"https://example.com/storage/v1/object/upload/sign/bucket/{path}"
            f"?token=token-{path}"
        )


def test_sync_create_signed_upload_urls_forwards_options() -> None:
    proxy = _sync_bucket_proxy()
    paths = ["folder/image.png", "solo.txt"]

    def fake_request(*args: Any, **kwargs: Any) -> Mock:
        return _mock_signed_upload_url_response("/".join(args[1][4:]))

    with patch.object(proxy, "_request", side_effect=fake_request) as request:
        proxy.create_signed_upload_urls(
            paths, options=CreateSignedUploadUrlOptions(upsert="true")
        )

    assert request.call_count == len(paths)
    for call in request.call_args_list:
        assert call.kwargs["headers"].get("x-upsert") == "true"


@pytest.mark.asyncio
async def test_async_create_signed_upload_urls_signs_each_path() -> None:
    proxy = _async_bucket_proxy()
    paths = ["folder/image.png", "nested/dir/photo.jpg", "solo.txt"]

    async def fake_request(*args: Any, **kwargs: Any) -> Mock:
        return _mock_signed_upload_url_response("/".join(args[1][4:]))

    with patch.object(
        proxy, "_request", new_callable=AsyncMock, side_effect=fake_request
    ) as request:
        results = await proxy.create_signed_upload_urls(paths)

    assert request.call_count == len(paths)
    assert len(results) == len(paths)
    for path, result in zip(paths, results):
        assert result["path"] == path
        assert result["token"] == f"token-{path}"
        assert result["signed_url"] == (
            f"https://example.com/storage/v1/object/upload/sign/bucket/{path}"
            f"?token=token-{path}"
        )
