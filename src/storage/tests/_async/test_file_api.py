from io import BufferedReader
from pathlib import Path
from typing import Generator
from unittest.mock import AsyncMock, MagicMock, Mock, mock_open, patch

import pytest
from httpx import Headers, HTTPStatusError, Request, Response
from storage3._async.file_api import AsyncBucketProxy
from storage3.exceptions import StorageApiError
from yarl import URL


@pytest.fixture
def mock_client() -> AsyncMock:
    return AsyncMock(headers=Headers())


@pytest.fixture
def file_api(mock_client: AsyncMock) -> AsyncBucketProxy:
    return AsyncBucketProxy(
        id="bucket",
        _base_url=URL("http://example.com"),
        _headers=Headers(),
        _client=mock_client,
    )


class _MalformedErrorBody(dict):
    """An error body missing message/error/statusCode, carrying .text like httpx responses."""

    text = "mock error body without error fields"


def _error_response() -> Mock:
    response = Mock(spec=Response)
    response.json.return_value = _MalformedErrorBody()
    response.raise_for_status = Mock(
        side_effect=HTTPStatusError(
            "Conflict",
            request=Mock(spec=Request),
            response=response,
        )
    )
    return response


def _success_response() -> Mock:
    response = Mock(spec=Response)
    response.raise_for_status = Mock()
    response.json.return_value = {"Key": "file.txt"}
    return response


def _make_file(tmp_path, name="data.bin", size=1024) -> Path:
    file_path = tmp_path / name
    file_path.write_bytes(b"x" * size)
    return file_path


@pytest.fixture
def opened_handle() -> Generator[Mock, None, None]:
    """A builtins.open mock whose returned handle passes the BufferedReader check."""
    m = mock_open(read_data=b"x" * 1024)
    m.return_value = MagicMock(spec=BufferedReader)
    with patch("builtins.open", m) as patched:
        yield patched


async def test_upload_closes_file_handle_on_error(
    mock_client: AsyncMock, file_api: AsyncBucketProxy, tmp_path, opened_handle
) -> None:
    """A handle storage3 opened itself must be closed even when the upload fails (#1575)."""
    mock_client.request.return_value = _error_response()

    with pytest.raises(StorageApiError):
        await file_api.upload("file.txt", str(_make_file(tmp_path)))

    opened_handle.return_value.close.assert_called_once()


async def test_upload_closes_file_handle_on_success(
    mock_client: AsyncMock, file_api: AsyncBucketProxy, tmp_path, opened_handle
) -> None:
    """Regression: the success path must keep closing the handle it opened."""
    mock_client.request.return_value = _success_response()

    response = await file_api.upload("file.txt", str(_make_file(tmp_path)))

    opened_handle.return_value.close.assert_called_once()
    assert response.fullPath == "file.txt"


async def test_update_closes_file_handle_on_error(
    mock_client: AsyncMock, file_api: AsyncBucketProxy, tmp_path, opened_handle
) -> None:
    """update() shares _upload_or_update, so it is affected the same way."""
    mock_client.request.return_value = _error_response()

    with pytest.raises(StorageApiError):
        await file_api.update("file.txt", str(_make_file(tmp_path)))

    opened_handle.return_value.close.assert_called_once()
