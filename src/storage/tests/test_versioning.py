import json
from collections.abc import Callable
from typing import Any

import pytest
from httpx import Request, Response
from supabase_utils.types import JSON

from storage3.types import FileVersion

from .utils import STORAGE_URL, call_with_client, use_async

BUCKET_JSON: dict[str, JSON] = {
    "id": "bucket",
    "name": "bucket",
    "owner": "",
    "public": False,
    "created_at": "2026-11-18T10:00:00Z",
    "updated_at": "2026-11-18T10:00:00Z",
    "file_size_limit": None,
    "allowed_mime_types": None,
}

OBJECT_JSON: dict[str, JSON] = {
    "id": "object-id",
    "version": "v1",
    "name": "a.txt",
    "bucket_id": "bucket",
    "created_at": "2026-11-18T10:00:00Z",
    "metadata": {},
    "archived_at": "2026-11-18T11:00:00Z",
    "is_delete_marker": False,
    "is_versioned": True,
}

DELETE_MARKER_JSON: dict[str, JSON] = {
    "id": "marker-id",
    "version": "v2",
    "name": "a.txt",
    "bucket_id": "bucket",
    "created_at": "2026-11-18T10:00:00Z",
    "metadata": None,
    "archived_at": None,
    "is_delete_marker": True,
    "is_versioned": True,
}


async def run(
    use_async: bool, action: Callable[[Any], Any], content: JSON
) -> tuple[Request, Any]:
    requests: list[Request] = []

    def handler(request: Request) -> Response:
        requests.append(request)
        return Response(200, json=content)

    result = await call_with_client(use_async, handler, action)
    (request,) = requests
    return request, result


@use_async
async def test_create_bucket_sends_the_versioning_status(use_async: bool) -> None:
    request, _ = await run(
        use_async,
        lambda client: client.create_bucket("bucket", versioning_status="ENABLED"),
        {"name": "bucket"},
    )
    assert json.loads(request.content) == {
        "id": "bucket",
        "name": "bucket",
        "versioning_status": "ENABLED",
    }


@use_async
async def test_create_bucket_leaves_the_versioning_status_to_the_server(
    use_async: bool,
) -> None:
    request, _ = await run(
        use_async, lambda client: client.create_bucket("bucket"), {"name": "bucket"}
    )
    assert "versioning_status" not in json.loads(request.content)


@use_async
async def test_update_bucket_sends_the_versioning_status(use_async: bool) -> None:
    request, _ = await run(
        use_async,
        lambda client: client.update_bucket("bucket", versioning_status="SUSPENDED"),
        {"message": "Successfully updated"},
    )
    assert request.method == "PUT"
    assert json.loads(request.content) == {
        "id": "bucket",
        "name": "bucket",
        "versioning_status": "SUSPENDED",
    }


@use_async
@pytest.mark.parametrize(
    ("sent", "expected"),
    [
        ({"versioning_status": "ENABLED"}, "ENABLED"),
        ({"versioning_status": "PAUSED"}, "PAUSED"),
        ({}, None),
    ],
    ids=["known", "unknown", "missing"],
)
async def test_get_bucket_reads_the_versioning_status(
    use_async: bool, sent: dict[str, JSON], expected: str | None
) -> None:
    _, bucket = await run(
        use_async, lambda client: client.get_bucket("bucket"), BUCKET_JSON | sent
    )
    assert bucket.versioning_status == expected


@use_async
async def test_info_sends_the_version_id_and_reads_the_version_fields(
    use_async: bool,
) -> None:
    request, info = await run(
        use_async,
        lambda client: client.from_("bucket").info("a.txt", version_id="v1"),
        OBJECT_JSON,
    )
    assert request.url.path == "/storage/v1/object/info/bucket/a.txt"
    assert dict(request.url.params) == {"versionId": "v1"}
    assert info.version == "v1"
    assert info.archived_at is not None
    assert info.is_delete_marker is False
    assert info.is_versioned is True


@use_async
async def test_info_sends_no_version_id_by_default(use_async: bool) -> None:
    request, _ = await run(
        use_async, lambda client: client.from_("bucket").info("a.txt"), OBJECT_JSON
    )
    assert request.url.query == b""


@use_async
async def test_download_sends_the_version_id(use_async: bool) -> None:
    requests: list[Request] = []

    def handler(request: Request) -> Response:
        requests.append(request)
        return Response(200, content=b"old")

    content = await call_with_client(
        use_async,
        handler,
        lambda client: client.from_("bucket").download("a.txt", version_id="v1"),
    )
    assert content == b"old"
    assert requests[0].url.path == "/storage/v1/object/bucket/a.txt"
    assert dict(requests[0].url.params) == {"versionId": "v1"}


@use_async
async def test_create_signed_url_sends_the_version_id(use_async: bool) -> None:
    request, url = await run(
        use_async,
        lambda client: client.from_("bucket").create_signed_url(
            "a.txt", 60, version_id="v1"
        ),
        {"signedURL": "/object/sign/bucket/a.txt?token=t"},
    )
    assert json.loads(request.content) == {"expiresIn": 60, "versionId": "v1"}
    assert url.endswith("/object/sign/bucket/a.txt?token=t")


async def test_get_public_url_appends_the_version_id() -> None:
    def handler(request: Request) -> Response:
        raise AssertionError("get_public_url must not send a request")

    url = await call_with_client(
        False,
        handler,
        lambda client: client.from_("bucket").get_public_url("a.txt", version_id="v1"),
    )
    assert url == f"{STORAGE_URL}object/public/bucket/a.txt?versionId=v1"


@use_async
@pytest.mark.parametrize("method", ["move", "copy"])
async def test_move_and_copy_send_the_source_version_id(
    use_async: bool, method: str
) -> None:
    request, _ = await run(
        use_async,
        lambda client: getattr(client.from_("bucket"), method)(
            "a.txt", "b.txt", source_version_id="v1"
        ),
        {"message": "ok", "Key": "bucket/b.txt", "Id": "id"},
    )
    assert json.loads(request.content) == {
        "bucketId": "bucket",
        "sourceKey": "a.txt",
        "destinationKey": "b.txt",
        "sourceVersionId": "v1",
    }


@use_async
async def test_remove_sends_paths_and_versions(use_async: bool) -> None:
    request, removed = await run(
        use_async,
        lambda client: client.from_("bucket").remove(
            ["/a.txt", FileVersion("/folder/b.txt", "v1")]
        ),
        [DELETE_MARKER_JSON],
    )
    assert json.loads(request.content) == {
        "prefixes": ["a.txt", {"path": "folder/b.txt", "versionId": "v1"}]
    }
    (marker,) = removed
    assert marker.is_delete_marker is True
    assert marker.metadata is None


@use_async
async def test_list_sends_the_version_options_and_reads_the_version_fields(
    use_async: bool,
) -> None:
    request, page = await run(
        use_async,
        lambda client: client.from_("bucket").list(
            noncurrent_versions="include", delete_markers="only"
        ),
        {
            "hasNext": False,
            "folders": [],
            "objects": [
                {
                    "id": "marker-id",
                    "name": "a.txt",
                    "updated_at": "2026-11-18T10:00:00Z",
                    "metadata": None,
                    "version": "v2",
                    "archived_at": None,
                    "is_delete_marker": True,
                    "is_versioned": True,
                }
            ],
        },
    )
    assert json.loads(request.content) == {
        "noncurrentVersions": "include",
        "deleteMarkers": "only",
    }
    (entry,) = page.objects
    assert entry.version == "v2"
    assert entry.archived_at is None
    assert entry.is_delete_marker is True
    assert entry.is_versioned is True


@use_async
async def test_pages_forwards_the_version_options(use_async: bool) -> None:
    options = {"noncurrent_versions": "only", "delete_markers": "exclude"}

    async def collect_async(client: Any) -> list[Any]:
        return [page async for page in client.from_("bucket").pages(**options)]

    def collect(client: Any) -> list[Any]:
        return list(client.from_("bucket").pages(**options))

    request, _ = await run(
        use_async,
        collect_async if use_async else collect,
        {"hasNext": False, "folders": [], "objects": []},
    )
    assert json.loads(request.content) == {
        "noncurrentVersions": "only",
        "deleteMarkers": "exclude",
    }
