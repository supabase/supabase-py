import pytest
from httpx import AsyncClient, Client, MockTransport, Request, Response
from storage3 import AsyncStorageClient, SyncStorageClient

URL = "https://example.supabase.co/storage/v1/"
HEADERS = {"Authorization": "Bearer jwt", "apikey": "key"}

PATHS = [
    ("file.png", "file.png"),
    ("folder/file.png", "folder/file.png"),
    ("/folder/file.png", "folder/file.png"),
    ("//folder/file.png", "folder/file.png"),
    ("backup-2024-01-01T10:00:00.sql", "backup-2024-01-01T10:00:00.sql"),
    ("user:42/avatar.png", "user:42/avatar.png"),
    ("folder/x:y.png", "folder/x:y.png"),
    ("what?.txt", "what%3F.txt"),
    ("report#1.pdf", "report%231.pdf"),
    ("a b.png", "a%20b.png"),
    ("a%20b.png", "a%20b.png"),
]


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
@pytest.mark.parametrize(("path", "expected"), PATHS)
async def test_upload_sends_the_whole_object_key(
    use_async: bool, path: str, expected: str
) -> None:
    requested = await _requested_path(use_async, path)
    assert requested == f"/storage/v1/object/bucket/{expected}"


@pytest.mark.asyncio
@pytest.mark.parametrize(("path", "expected"), PATHS)
async def test_get_public_url_keeps_the_whole_object_key(
    path: str, expected: str
) -> None:
    async_client = AsyncStorageClient(URL, HEADERS)
    sync_client = SyncStorageClient(URL, HEADERS)
    public_url = f"{URL}object/public/bucket/{expected}"

    assert await async_client.from_("bucket").get_public_url(path) == public_url
    assert sync_client.from_("bucket").get_public_url(path) == public_url


@pytest.mark.asyncio
@pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("path", ["report%FF.txt", "folder/report%FE.txt"])
async def test_invalid_percent_escapes_in_object_key_raise(
    use_async: bool, path: str
) -> None:
    with pytest.raises(UnicodeDecodeError):
        await _requested_path(use_async, path)


@pytest.mark.asyncio
@pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize(
    "path",
    [
        "folder/../report.txt",
        "folder?/../report.txt",
        "../../auth",
        "a/./b.png",
        "folder/%2E%2E/report.txt",
    ],
)
async def test_dot_segments_in_object_key_raise(use_async: bool, path: str) -> None:
    with pytest.raises(ValueError, match="dot segments"):
        await _requested_path(use_async, path)


@pytest.mark.parametrize("path", ["folder/../report.txt", "a/./b.png"])
def test_get_public_url_rejects_dot_segments(path: str) -> None:
    with pytest.raises(ValueError, match="dot segments"):
        SyncStorageClient(URL, HEADERS).from_("bucket").get_public_url(path)
