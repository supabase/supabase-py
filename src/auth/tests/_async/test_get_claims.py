import pytest
from httpx import AsyncClient, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import AsyncHttpxSession

from supabase_auth import AsyncSupabaseAuthClient
from supabase_auth.errors import AuthInvalidJwtError

from .conftest import base64url_segment

PAYLOAD = base64url_segment({"sub": "user", "exp": 9999999999})


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
        f"{base64url_segment({'typ': 'JWT'})}.{PAYLOAD}.sig",
        "\u00e9.\u00e9.\u00e9",
    ],
    ids=["opaque", "alg-missing", "non-ascii"],
)
async def test_get_claims_raises_auth_error_for_malformed_jwt(token: str) -> None:
    requests: list[Request] = []
    client = mock_client(requests)

    with pytest.raises(AuthInvalidJwtError, match=r"Invalid JWT structure"):
        await client.get_claims(token)

    assert requests == []
