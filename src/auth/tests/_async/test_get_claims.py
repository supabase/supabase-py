import base64
import json

import pytest
from httpx import AsyncClient, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import AsyncHttpxSession

from supabase_auth import AsyncSupabaseAuthClient
from supabase_auth.errors import AuthInvalidJwtError


def b64(value: object) -> str:
    raw = value if isinstance(value, bytes) else json.dumps(value).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


PAYLOAD = b64({"sub": "user", "exp": 9999999999})


def mock_client(requests: list[Request]) -> AsyncSupabaseAuthClient:
    def handler(request: Request) -> Response:
        requests.append(request)
        return Response(500)

    return AsyncSupabaseAuthClient(
        url="http://localhost",
        http_session=AsyncHttpxSession(
            client=AsyncClient(transport=MockTransport(handler))
        ),
        auto_refresh_token=False,
    )


@pytest.mark.parametrize(
    "token",
    [
        "opaque-token",
        f"{b64(b'not json')}.{PAYLOAD}.{b64(b'sig')}",
        f"{b64({'typ': 'JWT'})}.{PAYLOAD}.{b64(b'sig')}",
        f"{b64({'alg': 'HS256'})}.{b64(b'not json')}.{b64(b'sig')}",
        "a.b.c",
        "\u00e9.\u00e9.\u00e9",
    ],
    ids=[
        "opaque",
        "header-not-json",
        "alg-missing",
        "payload-not-json",
        "undecodable-base64",
        "non-ascii",
    ],
)
async def test_get_claims_raises_auth_error_for_malformed_jwt(token: str) -> None:
    requests: list[Request] = []
    client = mock_client(requests)

    with pytest.raises(AuthInvalidJwtError, match=r"Invalid JWT structure"):
        await client.get_claims(token)

    assert requests == []
