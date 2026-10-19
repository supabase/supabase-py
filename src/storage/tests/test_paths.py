from __future__ import annotations

import pytest
from httpx import AsyncClient, Client, Headers, MockTransport, Request, Response
from storage3._async.file_api import AsyncBucketProxy
from storage3._async.file_api import relative_path_to_parts as async_parts
from storage3._sync.file_api import SyncBucketProxy
from storage3._sync.file_api import relative_path_to_parts as sync_parts
from yarl import URL

BASE_URL = URL("http://localhost:54321/storage/v1/")


@pytest.mark.parametrize("relative_path_to_parts", [sync_parts, async_parts])
@pytest.mark.parametrize(
    "path, parts",
    [
        ("image.png", ("image.png",)),
        ("folder/image.png", ("folder", "image.png")),
        ("/folder/image.png", ("folder", "image.png")),
        ("a b/c d.png", ("a b", "c d.png")),
        ("folder/what?.png", ("folder", "what?.png")),
        ("folder/issue#1.png", ("folder", "issue#1.png")),
        ("folder/a?b=c#d.png", ("folder", "a?b=c#d.png")),
        ("folder/", ("folder", "")),
        ("/", ()),
        ("", ()),
    ],
)
def test_relative_path_to_parts(relative_path_to_parts, path, parts) -> None:
    assert relative_path_to_parts(path) == parts


def test_sync_special_characters_are_kept_in_the_request_path() -> None:
    requests: list[Request] = []

    def handler(request: Request) -> Response:
        requests.append(request)
        return Response(200, json={})

    bucket = SyncBucketProxy(
        "bucket", BASE_URL, Headers(), Client(transport=MockTransport(handler))
    )
    bucket.info("folder/what?.png")
    bucket.info("folder/issue#1.png")

    assert [r.url.raw_path for r in requests] == [
        b"/storage/v1/object/info/bucket/folder/what%3F.png",
        b"/storage/v1/object/info/bucket/folder/issue%231.png",
    ]


async def test_async_special_characters_are_kept_in_the_request_path() -> None:
    requests: list[Request] = []

    def handler(request: Request) -> Response:
        requests.append(request)
        return Response(200, json={})

    bucket = AsyncBucketProxy(
        "bucket", BASE_URL, Headers(), AsyncClient(transport=MockTransport(handler))
    )
    await bucket.info("folder/what?.png")
    await bucket.info("folder/issue#1.png")

    assert [r.url.raw_path for r in requests] == [
        b"/storage/v1/object/info/bucket/folder/what%3F.png",
        b"/storage/v1/object/info/bucket/folder/issue%231.png",
    ]
