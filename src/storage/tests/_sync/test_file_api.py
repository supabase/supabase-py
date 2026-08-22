from io import BufferedReader
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest
from httpx import Headers, HTTPStatusError, Request, Response
from storage3._sync.file_api import SyncBucketProxy
from storage3.exceptions import StorageApiError
from yarl import URL


@pytest.fixture
def mock_client() -> Mock:
    return Mock(headers=Headers())


@pytest.fixture
def file_api(mock_client: Mock) -> SyncBucketProxy:
    return SyncBucketProxy(
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


def test_upload_closes_file_handle_on_error(
    mock_client: Mock, file_api: SyncBucketProxy, tmp_path, opened_handle
) -> None:
    """A handle storage3 opened itself must be closed even when the upload fails (#1575)."""
    mock_client.request.return_value = _error_response()

    with pytest.raises(StorageApiError):
        file_api.upload("file.txt", str(_make_file(tmp_path)))

    opened_handle.return_value.close.assert_called_once()


def test_upload_closes_file_handle_on_success(
    mock_client: Mock, file_api: SyncBucketProxy, tmp_path, opened_handle
) -> None:
    """Regression: the success path must keep closing the handle it opened."""
    mock_client.request.return_value = _success_response()

    response = file_api.upload("file.txt", str(_make_file(tmp_path)))

    opened_handle.return_value.close.assert_called_once()
    assert response.fullPath == "file.txt"


def test_update_closes_file_handle_on_error(
    mock_client: Mock, file_api: SyncBucketProxy, tmp_path, opened_handle
) -> None:
    """update() shares _upload_or_update, so it is affected the same way."""
    mock_client.request.return_value = _error_response()

    with pytest.raises(StorageApiError):
        file_api.update("file.txt", str(_make_file(tmp_path)))

    opened_handle.return_value.close.assert_called_once()
