import base64
import dataclasses
import json
import re
from collections.abc import Callable
from typing import Any

import pytest
from httpx import Request, Response
from supabase_utils.http.io import AsyncHttpIO, SyncHttpIO
from supabase_utils.types import JSON

from storage3 import StorageFileApiClient
from storage3.exceptions import StorageApiError, StorageException
from storage3.types import SortBy, TransformOptions, UploadResponse

from .utils import STORAGE_URL, call_with_client, use_async

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


NOT_FOUND_BODIES = [
    (
        400,
        b'{"statusCode": "404", "error": "not_found", "message": "Object not found",'
        b' "code": "NoSuchKey"}',
    ),
    (
        404,
        b'{"statusCode": "404", "error": "not_found", "message": "Object not found",'
        b' "code": "NoSuchKey"}',
    ),
]


@use_async
@pytest.mark.parametrize(("status", "content"), NOT_FOUND_BODIES)
async def test_exists_false_when_the_object_is_not_found(
    use_async: bool, status: int, content: bytes
) -> None:
    results: list[bool] = []

    async def collect_async(b: StorageFileApiClient[AsyncHttpIO]) -> None:
        results.append(await b.exists("/folder/missing.txt"))

    def collect_sync(b: StorageFileApiClient[SyncHttpIO]) -> None:
        results.append(b.exists("/folder/missing.txt"))

    request = await run(
        use_async, collect_async if use_async else collect_sync, status, content
    )
    assert results == [False]
    assert request.method == "GET"
    assert request.url.path == "/storage/v1/object/info/bucket/folder/missing.txt"


@use_async
@pytest.mark.parametrize(
    ("status", "content", "code"),
    [
        (
            400,
            b'{"statusCode": "404", "error": "Bucket not found",'
            b' "message": "Bucket not found", "code": "NoSuchBucket"}',
            "NoSuchBucket",
        ),
        (
            400,
            b'{"statusCode": "403", "error": "Unauthorized",'
            b' "message": "invalid signature", "code": "InvalidJWT"}',
            "InvalidJWT",
        ),
        (
            400,
            b'{"statusCode": "404", "error": "not_found",'
            b' "message": "Bucket not found"}',
            "not_found",
        ),
        (401, b"", "InternalError"),
        (404, b"", "InternalError"),
    ],
)
async def test_exists_raises_other_errors(
    use_async: bool, status: int, content: bytes, code: str
) -> None:
    with pytest.raises(StorageApiError) as error:
        await run(use_async, lambda b: b.exists("missing.txt"), status, content)
    assert error.value.status_code == status
    assert error.value.code == code


@use_async
async def test_error_with_binary_body_raises_storage_api_error(use_async: bool) -> None:
    with pytest.raises(StorageApiError) as error:
        await run(use_async, lambda b: b.download("file.txt"), 502, b"\xff\xfe")
    assert error.value.status_code == 502


def empty_page_handler(requests: list[Request]) -> Callable[[Request], Response]:
    def handler(request: Request) -> Response:
        requests.append(request)
        return Response(200, json={"hasNext": False, "folders": [], "objects": []})

    return handler


@use_async
async def test_list_sends_the_given_options_to_list_v2(use_async: bool) -> None:
    requests: list[Request] = []

    result = await call_with_client(
        use_async,
        empty_page_handler(requests),
        lambda client: client.from_("bucket").list(
            "photos/", limit=2, cursor="opaque", with_delimiter=True
        ),
    )

    assert not result.hasNext
    assert result.nextCursor is None
    (request,) = requests
    assert request.method == "POST"
    assert request.url.path == "/storage/v1/object/list-v2/bucket"
    assert json.loads(request.content) == {
        "prefix": "photos/",
        "limit": 2,
        "cursor": "opaque",
        "with_delimiter": True,
    }


@use_async
async def test_list_sends_an_empty_body_by_default(use_async: bool) -> None:
    requests: list[Request] = []

    await call_with_client(
        use_async,
        empty_page_handler(requests),
        lambda client: client.from_("bucket").list(),
    )

    assert json.loads(requests[0].content) == {}


@use_async
async def test_list_returns_folder_rows_as_folders(use_async: bool) -> None:
    response_body: dict[str, JSON] = {
        "hasNext": True,
        "nextCursor": "opaque",
        "folders": [
            {
                "id": None,
                "name": "photos/2024/",
                "key": "2024",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-02T00:00:00Z",
                "last_accessed_at": None,
                "metadata": None,
            },
            {"id": None, "name": "photos/archive/"},
        ],
        "objects": [
            {
                "id": "object-id",
                "name": "photos/cat.png",
                "key": "cat.png",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "last_accessed_at": "2024-01-03T00:00:00Z",
                "metadata": {"mimetype": "image/png"},
            }
        ],
    }

    def handler(request: Request) -> Response:
        return Response(200, json=response_body)

    result = await call_with_client(
        use_async,
        handler,
        lambda client: client.from_("bucket").list("photos/", with_delimiter=True),
    )

    assert result.hasNext
    assert result.nextCursor == "opaque"
    assert [folder.name for folder in result.folders] == [
        "photos/2024/",
        "photos/archive/",
    ]
    assert result.folders[0].key == "2024"
    assert result.folders[0].created_at is not None
    assert result.folders[1].created_at is None
    assert result.folders[1].updated_at is None
    (object,) = result.objects
    assert object.id == "object-id"
    assert object.name == "photos/cat.png"
    assert object.key == "cat.png"
    assert object.last_accessed_at is not None
    assert object.metadata == {"mimetype": "image/png"}


@use_async
async def test_list_accepts_object_rows_without_created_at(use_async: bool) -> None:
    """Supabase Storage releases before v1.27.0 send no created_at."""
    response_body: dict[str, JSON] = {
        "hasNext": False,
        "folders": [],
        "objects": [
            {
                "id": "object-id",
                "name": "file.txt",
                "updated_at": "2024-01-01T00:00:00Z",
                "metadata": {"mimetype": "text/plain"},
            }
        ],
    }

    def handler(request: Request) -> Response:
        return Response(200, json=response_body)

    result = await call_with_client(
        use_async, handler, lambda client: client.from_("bucket").list()
    )

    (object,) = result.objects
    assert object.name == "file.txt"
    assert object.created_at is None
    assert object.last_accessed_at is None


@use_async
async def test_list_allows_null_object_metadata(use_async: bool) -> None:
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
        use_async, handler, lambda client: client.from_("bucket").list()
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
    ("caf\u00e9/\u00fc\u00f1\u00ee.png", "caf%C3%A9/%C3%BC%C3%B1%C3%AE.png"),
    ("folder/", "folder/"),
]

SIGNED_URL_RESPONSE = b'{"signedURL": "/object/sign/bucket/file.txt?token=t"}'
SIGNED_UPLOAD_URL_RESPONSE = (
    b'{"url": "/object/upload/sign/bucket/file.txt?token=t", "token": "t"}'
)


@use_async
@pytest.mark.parametrize(("path", "expected"), OBJECT_KEYS)
async def test_upload_sends_the_whole_object_key(
    use_async: bool, path: str, expected: str
) -> None:
    request = await run(use_async, lambda b: b.upload(path, b"hello"))
    assert request.url.raw_path.decode() == f"/storage/v1/object/bucket/{expected}"


@use_async
@pytest.mark.parametrize(("path", "expected"), OBJECT_KEYS)
async def test_download_sends_the_whole_object_key(
    use_async: bool, path: str, expected: str
) -> None:
    request = await run(use_async, lambda b: b.download(path), content=b"hello")
    assert request.url.raw_path.decode() == f"/storage/v1/object/bucket/{expected}"


@use_async
@pytest.mark.parametrize(("path", "expected"), OBJECT_KEYS)
async def test_create_signed_url_sends_the_whole_object_key(
    use_async: bool, path: str, expected: str
) -> None:
    request = await run(
        use_async,
        lambda b: b.create_signed_url(path, 60),
        content=SIGNED_URL_RESPONSE,
    )
    assert request.url.raw_path.decode() == f"/storage/v1/object/sign/bucket/{expected}"


@use_async
@pytest.mark.parametrize(("path", "expected"), OBJECT_KEYS)
async def test_create_signed_upload_url_sends_the_whole_object_key(
    use_async: bool, path: str, expected: str
) -> None:
    request = await run(
        use_async,
        lambda b: b.create_signed_upload_url(path),
        content=SIGNED_UPLOAD_URL_RESPONSE,
    )
    assert (
        request.url.raw_path.decode()
        == f"/storage/v1/object/upload/sign/bucket/{expected}"
    )


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
@pytest.mark.parametrize("method", ["move", "copy"])
async def test_move_and_copy_normalize_object_keys(
    use_async: bool, method: str
) -> None:
    request = await run(
        use_async,
        lambda b: getattr(b, method)("/from/a.txt", "//to/b.txt"),
        content=b'{"message": "ok", "Key": "bucket/to/b.txt", "Id": "id"}',
    )
    assert json.loads(request.content) == {
        "bucketId": "bucket",
        "sourceKey": "from/a.txt",
        "destinationKey": "to/b.txt",
    }


@use_async
async def test_remove_normalizes_object_keys(use_async: bool) -> None:
    request = await run(
        use_async, lambda b: b.remove(["/a.txt", "folder/b.txt"]), content=b"[]"
    )
    assert json.loads(request.content) == {"prefixes": ["a.txt", "folder/b.txt"]}


@use_async
async def test_create_signed_urls_normalizes_object_keys(use_async: bool) -> None:
    request = await run(
        use_async,
        lambda b: b.create_signed_urls(["/a.txt", "folder/b.txt"], 60),
        content=b"[]",
    )
    assert json.loads(request.content)["paths"] == ["a.txt", "folder/b.txt"]


INVALID_KEY_ACTIONS: list[Callable[[str], FileAction]] = [
    lambda path: lambda b: b.upload(path, b"hello"),
    lambda path: lambda b: b.download(path),
    lambda path: lambda b: b.create_signed_url(path, 60),
    lambda path: lambda b: b.create_signed_upload_url(path),
    lambda path: lambda b: b.upload_to_signed_url(path, "token", b"hello"),
    lambda path: lambda b: b.get_public_url(path),
    lambda path: lambda b: b.info(path),
    lambda path: lambda b: b.exists(path),
    lambda path: lambda b: b.update(path, b"hello"),
    lambda path: lambda b: b.move(path, "to.txt"),
    lambda path: lambda b: b.move("from.txt", path),
    lambda path: lambda b: b.copy(path, "to.txt"),
    lambda path: lambda b: b.copy("from.txt", path),
    lambda path: lambda b: b.remove([path]),
    lambda path: lambda b: b.create_signed_urls([path], 60),
]


@use_async
@pytest.mark.parametrize("make_action", INVALID_KEY_ACTIONS)
@pytest.mark.parametrize("path", ["folder/../report.txt", "a/./b.png"])
async def test_dot_segments_raise_in_every_method(
    use_async: bool, make_action: Callable[[str], FileAction], path: str
) -> None:
    with pytest.raises(ValueError, match="dot segments"):
        await run(use_async, make_action(path))


@use_async
@pytest.mark.parametrize("make_action", INVALID_KEY_ACTIONS)
@pytest.mark.parametrize("path", ["a//b.txt", "folder//", "/a//b/c.txt"])
async def test_empty_segments_in_object_key_raise(
    use_async: bool, make_action: Callable[[str], FileAction], path: str
) -> None:
    with pytest.raises(ValueError, match="empty segments"):
        await run(use_async, make_action(path))


@use_async
@pytest.mark.parametrize("make_action", INVALID_KEY_ACTIONS)
@pytest.mark.parametrize("path", ["", "/", "//"])
async def test_empty_object_key_raises(
    use_async: bool, make_action: Callable[[str], FileAction], path: str
) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        await run(use_async, make_action(path))


@use_async
@pytest.mark.parametrize(
    ("sort_by", "expected"),
    [
        (
            SortBy(column="created_at", order="desc"),
            {"column": "created_at", "order": "desc"},
        ),
        (SortBy(), {"column": "name", "order": "asc"}),
    ],
)
async def test_list_sends_sort_by(
    use_async: bool, sort_by: SortBy, expected: dict[str, str]
) -> None:
    requests: list[Request] = []

    await call_with_client(
        use_async,
        empty_page_handler(requests),
        lambda client: client.from_("bucket").list(sort_by=sort_by),
    )

    assert json.loads(requests[0].content) == {"sortBy": expected}


@pytest.mark.parametrize("options", [SortBy(), TransformOptions()])
def test_option_types_are_frozen(options: object) -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        options.order = "desc"  # pyrefly: ignore[missing-attribute]


async def run_returning(
    use_async: bool, action: FileAction, content: JSON
) -> tuple[Request, Any]:
    requests: list[Request] = []

    def handler(request: Request) -> Response:
        requests.append(request)
        return Response(200, json=content)

    result = await call_with_client(
        use_async, handler, lambda client: action(client.from_("bucket"))
    )
    (request,) = requests
    return request, result


UPLOAD_JSON: JSON = {"Key": "bucket/folder/a.txt", "Id": "object-id", "version": "v1"}


UPLOAD_ACTIONS: list[FileAction] = [
    lambda b: b.upload("/folder/a.txt", b"hello"),
    lambda b: b.update("/folder/a.txt", b"hello"),
]


@use_async
@pytest.mark.parametrize("action", UPLOAD_ACTIONS)
async def test_upload_and_update_return_the_object(
    use_async: bool, action: FileAction
) -> None:
    _, result = await run_returning(use_async, action, UPLOAD_JSON)
    assert result == UploadResponse(
        id="object-id",
        path="folder/a.txt",
        full_path="bucket/folder/a.txt",
        version="v1",
    )


@use_async
async def test_upload_to_signed_url_returns_the_object_without_an_id(
    use_async: bool,
) -> None:
    _, result = await run_returning(
        use_async,
        lambda b: b.upload_to_signed_url("folder/a.txt", "token", b"hello"),
        {"Key": "bucket/folder/a.txt", "version": "v1"},
    )
    assert result == UploadResponse(
        id=None, path="folder/a.txt", full_path="bucket/folder/a.txt", version="v1"
    )


@use_async
async def test_copy_sends_the_destination_options_and_returns_the_object(
    use_async: bool,
) -> None:
    request, result = await run_returning(
        use_async,
        lambda b: b.copy(
            "from/a.txt", "/to/b.txt", destination_bucket="other", upsert=True
        ),
        {"Key": "other/to/b.txt", "Id": "copy-id", "version": "v2", "name": "to/b.txt"},
    )
    assert json.loads(request.content) == {
        "bucketId": "bucket",
        "sourceKey": "from/a.txt",
        "destinationKey": "to/b.txt",
        "destinationBucket": "other",
    }
    assert request.headers["x-upsert"] == "true"
    assert "x-metadata" not in request.headers
    assert result == UploadResponse(
        id="copy-id", path="to/b.txt", full_path="other/to/b.txt", version="v2"
    )


@use_async
async def test_copy_without_upsert_sends_false(use_async: bool) -> None:
    request, _ = await run_returning(
        use_async, lambda b: b.copy("a.txt", "b.txt"), UPLOAD_JSON
    )
    assert request.headers["x-upsert"] == "false"


@use_async
async def test_copy_without_copy_metadata_sends_the_overrides(
    use_async: bool,
) -> None:
    request, _ = await run_returning(
        use_async,
        lambda b: b.copy(
            "a.txt",
            "b.txt",
            copy_metadata=False,
            metadata={"owner": "me", "tags": ["a"]},
            cache_control="max-age=60",
            content_type="text/csv",
            content_encoding="",
        ),
        UPLOAD_JSON,
    )
    assert json.loads(request.content) == {
        "bucketId": "bucket",
        "sourceKey": "a.txt",
        "destinationKey": "b.txt",
        "copyMetadata": False,
        "metadata": {
            "cacheControl": "max-age=60",
            "mimetype": "text/csv",
            "contentEncoding": "",
        },
    }
    assert json.loads(base64.b64decode(request.headers["x-metadata"])) == {
        "owner": "me",
        "tags": ["a"],
    }


@use_async
@pytest.mark.parametrize(
    ("cache_control", "expected"),
    [("3600", "max-age=3600"), ("no-cache", "no-cache")],
)
async def test_copy_sends_seconds_as_max_age(
    use_async: bool, cache_control: str, expected: str
) -> None:
    request, _ = await run_returning(
        use_async,
        lambda b: b.copy(
            "a.txt", "b.txt", copy_metadata=False, cache_control=cache_control
        ),
        UPLOAD_JSON,
    )
    assert json.loads(request.content)["metadata"] == {"cacheControl": expected}


@use_async
async def test_copy_without_copy_metadata_sends_only_the_flag(
    use_async: bool,
) -> None:
    request, _ = await run_returning(
        use_async, lambda b: b.copy("a.txt", "b.txt", copy_metadata=False), UPLOAD_JSON
    )
    assert json.loads(request.content) == {
        "bucketId": "bucket",
        "sourceKey": "a.txt",
        "destinationKey": "b.txt",
        "copyMetadata": False,
    }
    assert "x-metadata" not in request.headers


@use_async
@pytest.mark.parametrize(
    "overrides",
    [
        {"metadata": {}},
        {"cache_control": "max-age=60"},
        {"content_type": "text/csv"},
        {"content_encoding": "gzip"},
    ],
)
async def test_copy_overrides_require_copy_metadata_false(
    use_async: bool, overrides: dict[str, Any]
) -> None:
    with pytest.raises(ValueError, match="require copy_metadata=False"):
        await run(use_async, lambda b: b.copy("a.txt", "b.txt", **overrides))


@use_async
async def test_copy_rejects_non_bool_upsert(use_async: bool) -> None:
    with pytest.raises(TypeError, match="upsert must be a bool, not str"):
        await run(use_async, lambda b: b.copy("a.txt", "b.txt", upsert="true"))


@use_async
async def test_move_sends_the_destination_bucket(use_async: bool) -> None:
    request, _ = await run_returning(
        use_async,
        lambda b: b.move("a.txt", "b.txt", destination_bucket="other"),
        {"message": "Successfully moved"},
    )
    assert json.loads(request.content) == {
        "bucketId": "bucket",
        "sourceKey": "a.txt",
        "destinationKey": "b.txt",
        "destinationBucket": "other",
    }


def cursor_pages_handler(requests: list[Request]) -> Callable[[Request], Response]:
    pages: dict[str | None, dict[str, Any]] = {
        None: {
            "hasNext": True,
            "nextCursor": "second",
            "folders": [],
            "objects": [object_row("a.png")],
        },
        "second": {
            "hasNext": True,
            "nextCursor": "third",
            "folders": [],
            "objects": [object_row("b.png")],
        },
        "third": {
            "hasNext": False,
            "folders": [],
            "objects": [object_row("c.png")],
        },
    }

    def handler(request: Request) -> Response:
        requests.append(request)
        return Response(200, json=pages[json.loads(request.content).get("cursor")])

    return handler


def object_row(name: str) -> dict[str, Any]:
    return {
        "id": name,
        "name": name,
        "updated_at": "2026-01-01T00:00:00Z",
        "metadata": None,
    }


def collect_pages(use_async: bool, **options: Any) -> FileAction:
    if use_async:

        async def collect_async(client: Any) -> list[Any]:
            return [
                page async for page in client.from_("bucket").aiter_objects(**options)
            ]

        return collect_async

    def collect(client: Any) -> list[Any]:
        return list(client.from_("bucket").iter_objects(**options))

    return collect


@use_async
async def test_iter_objects_follows_the_cursor_of_each_page(use_async: bool) -> None:
    requests: list[Request] = []

    pages = await call_with_client(
        use_async,
        cursor_pages_handler(requests),
        collect_pages(use_async, prefix="photos/", limit=1, with_delimiter=True),
    )

    assert [[o.name for o in page.objects] for page in pages] == [
        ["a.png"],
        ["b.png"],
        ["c.png"],
    ]
    assert [json.loads(request.content) for request in requests] == [
        {"prefix": "photos/", "limit": 1, "with_delimiter": True},
        {"prefix": "photos/", "limit": 1, "with_delimiter": True, "cursor": "second"},
        {"prefix": "photos/", "limit": 1, "with_delimiter": True, "cursor": "third"},
    ]


@use_async
async def test_iter_objects_stops_after_a_single_page(use_async: bool) -> None:
    requests: list[Request] = []

    pages = await call_with_client(
        use_async, empty_page_handler(requests), collect_pages(use_async)
    )

    assert len(pages) == 1
    assert len(requests) == 1


@use_async
async def test_iter_objects_stops_when_a_page_has_no_cursor(use_async: bool) -> None:
    requests: list[Request] = []

    def handler(request: Request) -> Response:
        requests.append(request)
        return Response(200, json={"hasNext": True, "folders": [], "objects": []})

    pages = await call_with_client(use_async, handler, collect_pages(use_async))

    assert len(pages) == 1
    assert len(requests) == 1


async def test_iter_objects_fetches_a_page_only_when_it_is_reached() -> None:
    requests: list[Request] = []

    def take_first(client: Any) -> Any:
        return next(client.from_("bucket").iter_objects())

    first = await call_with_client(False, cursor_pages_handler(requests), take_first)

    assert [o.name for o in first.objects] == ["a.png"]
    assert len(requests) == 1


@use_async
async def test_iter_objects_raises_when_the_cursor_does_not_advance(
    use_async: bool,
) -> None:
    def handler(request: Request) -> Response:
        return Response(
            200,
            json={"hasNext": True, "nextCursor": "same", "folders": [], "objects": []},
        )

    with pytest.raises(StorageException, match="did not advance"):
        await call_with_client(use_async, handler, collect_pages(use_async))
