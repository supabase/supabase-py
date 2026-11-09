import dataclasses
import json
import re
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import pytest
from httpx import Request, Response
from supabase_utils.http.io import AsyncHttpIO, SyncHttpIO

from storage3 import StorageFileApiClient
from storage3.exceptions import StorageApiError
from storage3.types import SortByType, SortByV2, TransformOptions

from .utils import STORAGE_URL, call_with_client, use_async

if TYPE_CHECKING:
    from supabase_utils.types import JSON

FileAction = Callable[[Any], Any]


def form_fields(request: Request) -> dict[str, bytes]:
    content_type = request.headers["content-type"]
    boundary = content_type.split("boundary=")[1].encode()
    fields: dict[str, bytes] = {}
    for part in request.content.split(b"--" + boundary):
        header, _, body = part.partition(b"\r\n\r\n")
        if match := re.search(rb'name="([^"]+)"', header):
            fields[match.group(1).decode()] = body.removesuffix(b"\r\n")
    return fields


async def run(
    use_async: bool,
    action: FileAction,
    status: int = 200,
    content: bytes | None = None,
) -> Request:
    requests: list[Request] = []

    def handler(request: Request) -> Response:
        requests.append(request)
        if content is not None:
            return Response(status, content=content)
        return Response(status, json={"Key": "bucket/file.txt", "Id": "id"})

    await call_with_client(
        use_async, handler, lambda client: action(client.from_("bucket"))
    )
    assert len(requests) == 1
    return requests[0]


@use_async
async def test_upload_sends_default_cache_control_as_form_data(
    use_async: bool,
) -> None:
    request = await run(use_async, lambda b: b.upload("file.txt", b"hello"))
    assert "cache-control" not in request.headers
    assert form_fields(request)["cacheControl"] == b"3600"
    assert request.headers["x-upsert"] == "false"


@use_async
async def test_upload_sends_custom_cache_control_as_form_data(
    use_async: bool,
) -> None:
    request = await run(
        use_async,
        lambda b: b.upload(
            "file.txt",
            b"hello",
            cache_control="86400",
            headers={"x-custom-header": "custom-value"},
        ),
    )
    assert "cache-control" not in request.headers
    assert form_fields(request)["cacheControl"] == b"86400"
    assert request.headers["x-custom-header"] == "custom-value"


@use_async
async def test_update_sends_cache_control_as_form_data(use_async: bool) -> None:
    request = await run(
        use_async, lambda b: b.update("file.txt", b"hello", cache_control="7200")
    )
    assert request.method == "PUT"
    assert "cache-control" not in request.headers
    assert form_fields(request)["cacheControl"] == b"7200"
    assert "x-upsert" not in request.headers


@use_async
async def test_signed_upload_sends_default_cache_control(use_async: bool) -> None:
    request = await run(
        use_async, lambda b: b.upload_to_signed_url("file.txt", "token", b"hello")
    )
    assert "cache-control" not in request.headers
    assert form_fields(request)["cacheControl"] == b"3600"


@use_async
async def test_upload_to_signed_url_forwards_all_file_options(
    use_async: bool,
) -> None:
    request = await run(
        use_async,
        lambda b: b.upload_to_signed_url(
            "file.txt",
            "token",
            b"hello",
            cache_control="86400",
            content_type="text/custom",
            metadata={"owner": "alice"},
            headers={"x-custom-header": "custom-value"},
        ),
    )
    fields = form_fields(request)
    assert fields["cacheControl"] == b"86400"
    assert fields["metadata"].replace(b" ", b"") == b'{"owner":"alice"}'
    assert request.headers["x-custom-header"] == "custom-value"
    assert "cache-control" not in request.headers
    assert "x-metadata" not in request.headers
    assert b"Content-Type: text/custom" in request.content
    assert request.url.params["token"] == "token"


@use_async
@pytest.mark.parametrize(("upsert", "expected"), [(True, "true"), (False, "false")])
async def test_upload_sends_upsert_header(
    use_async: bool, upsert: bool, expected: str
) -> None:
    request = await run(
        use_async, lambda b: b.upload("file.txt", b"hello", upsert=upsert)
    )
    assert request.headers.get_list("x-upsert") == [expected]


@use_async
@pytest.mark.parametrize(
    ("upsert", "expected"), [(None, []), (True, ["true"]), (False, ["false"])]
)
async def test_create_signed_upload_url_sends_upsert_header(
    use_async: bool, upsert: bool | None, expected: list[str]
) -> None:
    request = await run(
        use_async,
        lambda b: b.create_signed_upload_url("file.txt", upsert=upsert),
        content=b'{"url": "/object/upload/sign/bucket/file.txt?token=t", "token": "t"}',
    )
    assert request.headers.get_list("x-upsert") == expected


STRING_UPSERT_ACTIONS: list[FileAction] = [
    lambda b: b.upload("file.txt", b"hello", upsert="false"),
    lambda b: b.create_signed_upload_url("file.txt", upsert="false"),
]


@use_async
@pytest.mark.parametrize("action", STRING_UPSERT_ACTIONS)
async def test_upsert_rejects_non_bool(use_async: bool, action: FileAction) -> None:
    with pytest.raises(TypeError, match="upsert must be a bool, not str"):
        await run(use_async, action)


@use_async
async def test_upload_headers_override_defaults(use_async: bool) -> None:
    request = await run(
        use_async,
        lambda b: b.upload("file.txt", b"hello", headers={"x-upsert": "true"}),
    )
    assert request.headers.get_list("x-upsert") == ["true"]


@use_async
@pytest.mark.parametrize("status", [400, 404])
async def test_exists_false_on_headless_error(use_async: bool, status: int) -> None:
    results: list[bool] = []

    async def collect_async(b: StorageFileApiClient[AsyncHttpIO]) -> None:
        results.append(await b.exists("missing.txt"))

    def collect_sync(b: StorageFileApiClient[SyncHttpIO]) -> None:
        results.append(b.exists("missing.txt"))

    await run(use_async, collect_async if use_async else collect_sync, status, b"")
    assert results == [False]


@use_async
async def test_exists_reraises_unexpected_status(use_async: bool) -> None:
    with pytest.raises(StorageApiError) as error:
        await run(use_async, lambda b: b.exists("missing.txt"), 401, b"")
    assert error.value.status_code == 401


@use_async
async def test_error_with_binary_body_raises_storage_api_error(use_async: bool) -> None:
    with pytest.raises(StorageApiError) as error:
        await run(use_async, lambda b: b.download("file.txt"), 502, b"\xff\xfe")
    assert error.value.status_code == 502


@use_async
async def test_list_v2_allows_null_object_metadata(use_async: bool) -> None:
    response_body: dict[str, JSON] = {
        "hasNext": False,
        "folders": [],
        "objects": [
            {
                "id": "object-without-metadata",
                "name": "file-without-metadata.txt",
                "updated_at": "2024-01-01T00:00:00Z",
                "created_at": "2024-01-01T00:00:00Z",
                "metadata": None,
            },
            {
                "id": "object-with-metadata",
                "name": "file-with-metadata.txt",
                "updated_at": "2024-01-01T00:00:00Z",
                "created_at": "2024-01-01T00:00:00Z",
                "metadata": {"mimetype": "text/plain"},
            },
        ],
    }

    def handler(request: Request) -> Response:
        return Response(200, json=response_body)

    result = await call_with_client(
        use_async, handler, lambda client: client.from_("bucket").list_v2()
    )

    assert len(result.objects) == 2
    assert result.objects[0].name == "file-without-metadata.txt"
    assert result.objects[0].metadata is None
    assert result.objects[1].metadata == {"mimetype": "text/plain"}


OBJECT_KEYS = [
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
    ("a%20b.png", "a%2520b.png"),
    ("a%2Fb.png", "a%252Fb.png"),
    ("folder/%2E%2E/report.txt", "folder/%252E%252E/report.txt"),
]


@use_async
@pytest.mark.parametrize(("path", "expected"), OBJECT_KEYS)
async def test_upload_sends_the_whole_object_key(
    use_async: bool, path: str, expected: str
) -> None:
    request = await run(use_async, lambda b: b.upload(path, b"hello"))
    assert request.url.raw_path.decode() == f"/storage/v1/object/bucket/{expected}"


@pytest.mark.parametrize(("path", "expected"), OBJECT_KEYS)
async def test_get_public_url_keeps_the_whole_object_key(
    path: str, expected: str
) -> None:
    def handler(request: Request) -> Response:
        raise AssertionError("get_public_url must not send a request")

    url = await call_with_client(
        False, handler, lambda client: client.from_("bucket").get_public_url(path)
    )
    assert url == f"{STORAGE_URL}object/public/bucket/{expected}"


@use_async
@pytest.mark.parametrize(
    "path",
    [
        "folder/../report.txt",
        "folder?/../report.txt",
        "../../auth",
        "a/./b.png",
        ".",
    ],
)
async def test_dot_segments_in_object_key_raise(use_async: bool, path: str) -> None:
    with pytest.raises(ValueError, match="dot segments"):
        await run(use_async, lambda b: b.upload(path, b"hello"))


@pytest.mark.parametrize("path", ["folder/../report.txt", "a/./b.png"])
async def test_get_public_url_rejects_dot_segments(path: str) -> None:
    def handler(request: Request) -> Response:
        raise AssertionError("get_public_url must not send a request")

    with pytest.raises(ValueError, match="dot segments"):
        await call_with_client(
            False, handler, lambda client: client.from_("bucket").get_public_url(path)
        )


@use_async
@pytest.mark.parametrize(
    ("sort_by", "expected"),
    [
        (
            SortByV2(column="created_at", order="desc"),
            {"column": "created_at", "order": "desc"},
        ),
        (SortByV2(), {"column": "name", "order": "asc"}),
    ],
)
async def test_list_v2_sends_sort_by(
    use_async: bool, sort_by: SortByV2, expected: dict[str, str]
) -> None:
    requests: list[Request] = []

    def handler(request: Request) -> Response:
        requests.append(request)
        return Response(200, json={"hasNext": False, "folders": [], "objects": []})

    await call_with_client(
        use_async,
        handler,
        lambda client: client.from_("bucket").list_v2(sort_by=sort_by),
    )

    assert json.loads(requests[0].content) == {"sortBy": expected}


@pytest.mark.parametrize("options", [SortByType(), SortByV2(), TransformOptions()])
def test_option_types_are_frozen(options: object) -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        options.order = "desc"  # pyrefly: ignore[missing-attribute]
