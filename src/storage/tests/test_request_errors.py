from typing import Any, Callable, Union

import pytest
from httpx import AsyncClient, Client, MockTransport, Request, Response
from storage3 import AsyncStorageClient, SyncStorageClient
from storage3.exceptions import StorageApiError

URL = "https://example.supabase.co/storage/v1/"

ANALYTICS_CALLS: dict[str, Callable[[Any], Any]] = {
    "create": lambda analytics: analytics.create("events"),
    "list": lambda analytics: analytics.list(),
    "delete": lambda analytics: analytics.delete("events"),
}


async def _raised_error(
    use_async: bool, response: Response, call: Callable[[Any], Any]
) -> StorageApiError:
    def handler(request: Request) -> Response:
        return response

    transport = MockTransport(handler)
    with pytest.raises(StorageApiError) as exc_info:
        if use_async:
            async with AsyncClient(transport=transport) as http:
                await call(AsyncStorageClient(URL, {}, http_client=http))
        else:
            with Client(transport=transport) as sync_http:
                call(SyncStorageClient(URL, {}, http_client=sync_http))
    return exc_info.value


@pytest.mark.asyncio
@pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("method", list(ANALYTICS_CALLS))
async def test_analytics_error_has_server_message(use_async: bool, method: str) -> None:
    body = {
        "error": {"message": "Bucket not found", "type": "NoSuchBucket", "code": 404}
    }

    def call(client: Any) -> Any:
        return ANALYTICS_CALLS[method](client.analytics())

    error = await _raised_error(use_async, Response(404, json=body), call)

    assert error.message == "Bucket not found"
    assert error.code == "NoSuchBucket"
    assert error.status == 404


@pytest.mark.asyncio
@pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize(
    ("response_body", "message", "code", "status"),
    [
        (
            {
                "statusCode": "404",
                "error": "Not Found",
                "message": "Vector bucket not found",
                "code": "NoSuchBucket",
            },
            "Vector bucket not found",
            "NoSuchBucket",
            "404",
        ),
        (
            "Bad Gateway",
            "The request failed, but could not parse error message response:'Bad Gateway'",
            "LibraryError",
            404,
        ),
    ],
    ids=["flat", "not-json"],
)
async def test_vector_error_formats(
    use_async: bool,
    response_body: Union[dict[str, str], str],
    message: str,
    code: str,
    status: Union[int, str],
) -> None:
    def call(client: Any) -> Any:
        return client.vectors().create_bucket("catalog")

    response = (
        Response(404, text=response_body)
        if isinstance(response_body, str)
        else Response(404, json=response_body)
    )
    error = await _raised_error(use_async, response, call)

    assert error.message == message
    assert error.code == code
    assert error.status == status
