import pytest
from httpx import AsyncClient, Client, MockTransport, Request, Response
from storage3 import AsyncStorageClient, SyncStorageClient

URL = "https://example.supabase.co/storage/v1/"
HEADERS = {"Authorization": "Bearer jwt", "apikey": "key"}


async def _requested_path(use_async: bool, path: str) -> str:
    sent: list[Request] = []

    def handler(request: Request) -> Response:
        sent.append(request)
        return Response(200, json={"Key": f"bucket/{path}", "Id": "id"})

    transport = MockTransport(handler)
    if use_async:
        async with AsyncClient(transport=transport) as http:
            client = AsyncStorageClient(URL, HEADERS, http_client=http)
            await client.from_("bucket").upload(path, b"hello")
    else:
        with Client(transport=transport) as sync_http:
            sync_client = SyncStorageClient(URL, HEADERS, http_client=sync_http)
            sync_client.from_("bucket").upload(path, b"hello")

    assert len(sent) == 1
    return sent[0].url.raw_path.decode()


@pytest.mark.asyncio
@pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize(
    ("path", "expected"),
    [
        (
            "backup-2024-01-01T10:00:00.sql",
            "/storage/v1/object/bucket/backup-2024-01-01T10:00:00.sql",
        ),
        ("user:42/avatar.png", "/storage/v1/object/bucket/user:42/avatar.png"),
        ("folder/x:y.png", "/storage/v1/object/bucket/folder/x:y.png"),
        ("/folder/file.png", "/storage/v1/object/bucket/folder/file.png"),
    ],
)
async def test_upload_keeps_colons_in_the_first_path_segment(
    use_async: bool, path: str, expected: str
) -> None:
    assert await _requested_path(use_async, path) == expected
