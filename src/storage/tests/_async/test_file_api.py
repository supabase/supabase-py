from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
from httpx import Headers, HTTPStatusError, Request, Response
from storage3.exceptions import StorageApiError
from yarl import URL

from .. import AsyncBucketProxy


def _error_response() -> Mock:
    response = Mock(spec=Response)
    response.status_code = 409
    response.json.return_value = {
        "message": "The resource already exists",
        "error": "Duplicate",
        "statusCode": 409,
    }
    response.raise_for_status = Mock(
        side_effect=HTTPStatusError(
            "Conflict", request=Mock(spec=Request), response=response
        )
    )
    return response


def _success_response() -> Mock:
    response = Mock(spec=Response)
    response.status_code = 200
    response.json.return_value = {"Key": "bucket/upload.txt"}
    response.raise_for_status = Mock()
    return response


def _proxy(response: Mock, captured: dict) -> AsyncBucketProxy:
    """A proxy whose transport records the `files` mapping storage3 built for the request."""

    async def request(*args: Any, **kwargs: Any) -> Mock:
        captured["files"] = kwargs["files"]
        return response

    client = Mock(headers=Headers())
    client.request = request
    return AsyncBucketProxy("bucket", URL("http://example.com"), Headers(), client)


@pytest.fixture
def source(tmp_path: Path) -> str:
    path = tmp_path / "upload.txt"
    path.write_bytes(b"payload")
    return str(path)


async def test_upload_closes_file_handle_on_error(source: str) -> None:
    """A handle storage3 opened itself must be closed when the upload fails."""
    captured: dict = {}

    with pytest.raises(StorageApiError):
        await _proxy(_error_response(), captured).upload("upload.txt", source)

    assert captured["files"]["file"][1].closed


async def test_upload_closes_file_handle_on_success(source: str) -> None:
    """Regression: the success path must keep closing the handle it opened."""
    captured: dict = {}

    await _proxy(_success_response(), captured).upload("upload.txt", source)

    assert captured["files"]["file"][1].closed


async def test_update_closes_file_handle_on_error(source: str) -> None:
    """update() shares _upload_or_update, so it leaks the same way."""
    captured: dict = {}

    with pytest.raises(StorageApiError):
        await _proxy(_error_response(), captured).update("upload.txt", source)

    assert captured["files"]["file"][1].closed


async def test_caller_supplied_handle_is_left_open(source: str) -> None:
    """storage3 must not close a stream the caller owns, on either path."""
    captured: dict = {}

    with open(source, "rb") as handle:
        with pytest.raises(StorageApiError):
            await _proxy(_error_response(), captured).upload("upload.txt", handle)
        assert not handle.closed

        await _proxy(_success_response(), captured).upload("upload.txt", handle)
        assert not handle.closed
