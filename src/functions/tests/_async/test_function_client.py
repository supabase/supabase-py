from types import TracebackType

import pytest
from supabase_utils.http.headers import Headers
from supabase_utils.http.io import AsyncHttpIO

# Import the class to test
from supabase_utils.http.request import Request, Response
from yarl import URL

from supabase_functions.client import AsyncFunctionsClient, FunctionsClient
from supabase_functions.errors import FunctionsHttpError, FunctionsRelayError
from supabase_functions.utils import FunctionRegion
from supabase_functions.version import __version__


def client_returning(
    content: bytes, status: int, headers: Headers | None = None
) -> FunctionsClient[AsyncHttpIO]:
    class MockHttpClient:
        async def send(self, request: Request) -> Response:
            return Response(
                headers=headers or Headers.empty(),
                status=status,
                content=content,
                request=request,
            )

        async def __aenter__(self) -> "MockHttpClient":
            return self

        async def __aexit__(
            self,
            exc_type: type[Exception] | None,
            exc: Exception | None,
            tb: TracebackType | None,
        ) -> None:
            pass

    return FunctionsClient(
        url=URL("https://supabase.com"),
        headers={},
        executor=AsyncHttpIO(session=MockHttpClient()),
    )


async def test_init_with_valid_params() -> None:
    valid_url = "https://supabase.com"
    client = AsyncFunctionsClient(url=valid_url, headers={})
    assert str(client.base_url) == valid_url
    assert "X-Client-Info" in client.default_headers
    assert (
        client.default_headers["X-Client-Info"]
        == f"supabase-py/supabase_functions v{__version__}"
    )


@pytest.mark.parametrize("invalid_url", ["not-a-url", "ftp://invalid.com", ""])
def test_init_with_invalid_url(invalid_url: str) -> None:
    with pytest.raises(Exception, match="url must be a valid HTTP URL string"):
        AsyncFunctionsClient(url=invalid_url, headers={})


async def test_set_auth_valid_token() -> None:
    client = client_returning(content=b'{"message": "success"}', status=200)
    valid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
    assert client.default_headers.get("Authorization") is None
    client.set_auth("")
    assert (
        client.default_headers["Authorization"] == "Bearer "
    )  # just to ensure that authorization field is non-empty beforehand
    client.set_auth(valid_token)
    assert client.default_headers["Authorization"] == f"Bearer {valid_token}"


async def test_invoke_success_json() -> None:
    client = client_returning(content=b'{"message": "success"}', status=200)
    response = await client.invoke("test-function", body={"test": "data"})
    assert response.content == b'{"message": "success"}'
    assert response.request.headers["Content-Type"] == "application/json"


async def test_invoke_success_binary() -> None:
    client = client_returning(content=b"binary content", status=200)
    response = await client.invoke("test-function")
    assert response.content == b"binary content"


async def test_invoke_with_region() -> None:
    client = client_returning(content=b'{"message": "success"}', status=200)
    response = await client.invoke("test-function", region=FunctionRegion.UsEast1)
    assert response.request.headers["x-region"] == "us-east-1"
    # Check that the URL contains the forceFunctionRegion query parameter
    assert response.request.url.query["forceFunctionRegion"] == "us-east-1"


async def test_invoke_with_http_error() -> None:
    client = client_returning(content=b'{"error": "Custom error message"}', status=400)
    with pytest.raises(FunctionsHttpError):
        await client.invoke("test-function")


async def test_invoke_with_relay_error() -> None:
    client = client_returning(
        content=b'{"error": "Relay error message"}',
        status=400,
        headers=Headers.from_mapping({"x-relay-header": "true"}),
    )
    with pytest.raises(FunctionsRelayError):
        await client.invoke("test-function")


async def test_invoke_invalid_function_name() -> None:
    client = client_returning(content=b'{"message": "success"}', status=200)
    with pytest.raises(ValueError, match="function_name must a valid string value."):
        await client.invoke("")


async def test_invoke_with_string_body() -> None:
    client = client_returning(content=b'{"message": "success"}', status=200)
    response = await client.invoke("test-function", body="string data")
    assert response.request.headers["Content-Type"] == "text/plain; charset=utf-8"


async def test_invoke_with_json_body() -> None:
    client = client_returning(content=b'{"message": "success"}', status=200)
    response = await client.invoke("test-function", body={"key": "value"})
    assert response.request.headers["Content-Type"] == "application/json"
