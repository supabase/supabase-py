import re
from typing import Dict

import pytest
from supabase_utils.http.headers import Headers
from supabase_utils.http.request import JSONRequest
from yarl import URL

from supabase_functions import AsyncFunctionsClient, SyncFunctionsClient, create_client


@pytest.fixture
def valid_url() -> str:
    return "https://example.com"


@pytest.fixture
def valid_headers() -> Dict[str, str]:
    return {"Authorization": "Bearer test_token", "Content-Type": "application/json"}


_X_CLIENT_INFO_PATTERN = re.compile(
    r"^supabase-py/supabase_functions v\S+; platform=.+; platform-version=.+; runtime=python; runtime-version=\S+$"
)


def test_async_x_client_info_structured_format(
    valid_url: str, valid_headers: Dict[str, str]
) -> None:
    client = AsyncFunctionsClient(url=valid_url, headers=valid_headers)
    x_client_info = client.default_headers.get("X-Client-Info")
    assert x_client_info is not None
    assert _X_CLIENT_INFO_PATTERN.match(x_client_info), (
        f"X-Client-Info format is wrong: {x_client_info}"
    )


def test_sync_x_client_info_structured_format(
    valid_url: str, valid_headers: Dict[str, str]
) -> None:
    client = SyncFunctionsClient(url=valid_url, headers=valid_headers)
    x_client_info = client.default_headers.get("X-Client-Info")
    assert x_client_info is not None
    assert _X_CLIENT_INFO_PATTERN.match(x_client_info), (
        f"X-Client-Info format is wrong: {x_client_info}"
    )


def test_create_async_client(valid_url: str, valid_headers: Dict[str, str]) -> None:
    # Test creating async client with explicit verify=True
    client = create_client(url=valid_url, headers=valid_headers, is_async=True)

    assert isinstance(client, AsyncFunctionsClient)
    assert str(client.base_url) == valid_url
    assert all(
        client.default_headers[key] == value for key, value in valid_headers.items()
    )


def test_create_sync_client(valid_url: str, valid_headers: Dict[str, str]) -> None:
    client = create_client(url=valid_url, headers=valid_headers, is_async=False)

    assert isinstance(client, SyncFunctionsClient)
    assert str(client.base_url) == valid_url
    assert all(
        client.default_headers[key] == value for key, value in valid_headers.items()
    )


def test_type_hints() -> None:
    from typing import get_type_hints

    hints = get_type_hints(create_client)

    assert hints["url"] is str
    assert hints["headers"] == dict[str, str]
    assert hints["is_async"] is bool
    assert hints["return"] == AsyncFunctionsClient | SyncFunctionsClient


def test_json_request_body_type_wins_over_client_default_content_type() -> None:
    request = JSONRequest(path=["x"], method="POST", body={"a": 1}).finalize(
        URL("https://example.com"), Headers.from_mapping({"Content-Type": "text/plain"})
    )
    assert request.headers.get_list("Content-Type") == ["application/json"]


def test_json_request_keeps_request_content_type() -> None:
    request = JSONRequest(
        path=["x"],
        method="POST",
        body={"a": 1},
        headers=Headers.from_mapping({"Content-Type": "application/merge-patch+json"}),
    ).finalize(URL("https://example.com"), Headers.empty())
    assert request.headers.get_list("Content-Type") == ["application/merge-patch+json"]
