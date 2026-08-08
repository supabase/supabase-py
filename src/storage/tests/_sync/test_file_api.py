from __future__ import annotations

import httpx
import pytest
from httpx import Headers
from storage3._sync.file_api import SyncBucketProxy
from storage3.exceptions import StorageApiError
from yarl import URL


def test_request_raises_real_error_when_body_missing_message_field() -> None:
    """A non-2xx body without message/error/statusCode must surface as StorageApiError."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"code": "TooLarge"}, request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        proxy = SyncBucketProxy(
            id="bucket",
            _base_url=URL("http://localhost:54321/storage/v1"),
            _headers=Headers(),
            _client=client,
        )
        with pytest.raises(StorageApiError) as exc_info:
            proxy._request("GET", ["object", "open", "bucket", "file.txt"])

    assert exc_info.value.code == "InternalError"
    assert exc_info.value.status == 400
    assert "TooLarge" in exc_info.value.message
