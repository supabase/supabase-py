from typing import Optional
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from starlette.requests import Request


def _make_request(auth_header: Optional[str]) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(b"authorization", auth_header.encode())] if auth_header else [],
    }
    return Request(scope)


@pytest.mark.asyncio
async def test_get_client_raises_401_when_no_auth_header():
    from dependencies import get_client
    request = _make_request(None)
    with pytest.raises(HTTPException) as exc_info:
        await get_client(request)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_client_raises_401_when_not_bearer():
    from dependencies import get_client
    request = _make_request("Basic dXNlcjpwYXNz")
    with pytest.raises(HTTPException) as exc_info:
        await get_client(request)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_client_raises_401_for_bearer_with_no_token():
    from dependencies import get_client
    request = _make_request("Bearer ")
    with pytest.raises(HTTPException) as exc_info:
        await get_client(request)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_client_returns_client_with_jwt():
    mock_client = AsyncMock()
    with patch("dependencies.acreate_client", AsyncMock(return_value=mock_client)):
        from dependencies import get_client
        request = _make_request("Bearer my-test-jwt")
        result = await get_client(request)
    assert result is mock_client
