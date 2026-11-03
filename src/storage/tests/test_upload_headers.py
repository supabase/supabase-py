from typing import Any

import pytest
from httpx import AsyncClient, Client, MockTransport, Request, Response
from storage3 import AsyncStorageClient, SyncStorageClient

URL = "https://example.supabase.co/storage/v1/"
CLIENT_HEADERS = {"Authorization": "Bearer client-jwt", "apikey": "client-key"}

UPLOAD_CALLS = {
    "upload": lambda bucket, options: bucket.upload("file.txt", b"hello", options),
    "update": lambda bucket, options: bucket.update("file.txt", b"hello", options),
    "upload_to_signed_url": lambda bucket, options: bucket.upload_to_signed_url(
        "file.txt", "token", b"hello", options
    ),
}


async def _sent_request(
    use_async: bool,
    method: str,
    options: Any,
    http_client_headers: dict[str, str] | None = None,
) -> Request:
    sent: list[Request] = []

    def handler(request: Request) -> Response:
        sent.append(request)
        return Response(200, json={"Key": "bucket/file.txt", "Id": "id"})

    transport = MockTransport(handler)
    call = UPLOAD_CALLS[method]
    if use_async:
        async with AsyncClient(
            transport=transport, headers=http_client_headers
        ) as http:
            client = AsyncStorageClient(URL, CLIENT_HEADERS, http_client=http)
            await call(client.from_("bucket"), options)
    else:
        with Client(transport=transport, headers=http_client_headers) as sync_http:
            sync_client = SyncStorageClient(URL, CLIENT_HEADERS, http_client=sync_http)
            call(sync_client.from_("bucket"), options)

    assert len(sent) == 1
    return sent[0]


@pytest.mark.asyncio
@pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("method", list(UPLOAD_CALLS))
@pytest.mark.parametrize("header_name", ["Authorization", "authorization"])
async def test_upload_headers_override_client_headers(
    use_async: bool, method: str, header_name: str
) -> None:
    options = {"headers": {header_name: "Bearer user-jwt"}}

    request = await _sent_request(use_async, method, options)

    assert request.headers.get_list("authorization") == ["Bearer user-jwt"]
    assert request.headers["apikey"] == "client-key"


@pytest.mark.asyncio
@pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("method", list(UPLOAD_CALLS))
async def test_upload_headers_override_non_authorization_client_header(
    use_async: bool, method: str
) -> None:
    options = {"headers": {"apikey": "user-key"}}

    request = await _sent_request(use_async, method, options)

    assert request.headers.get_list("apikey") == ["user-key"]
    assert request.headers.get_list("authorization") == ["Bearer client-jwt"]


@pytest.mark.asyncio
@pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("method", list(UPLOAD_CALLS))
async def test_upload_client_headers_override_http_client_headers(
    use_async: bool, method: str
) -> None:
    request = await _sent_request(
        use_async, method, None, {"Authorization": "Bearer http-client-jwt"}
    )

    assert request.headers.get_list("authorization") == ["Bearer client-jwt"]


@pytest.mark.asyncio
@pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("method", list(UPLOAD_CALLS))
async def test_upload_without_headers_sends_client_headers(
    use_async: bool, method: str
) -> None:
    request = await _sent_request(use_async, method, None)

    assert request.headers.get_list("authorization") == ["Bearer client-jwt"]
    assert request.headers["apikey"] == "client-key"
