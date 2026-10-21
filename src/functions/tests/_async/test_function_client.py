import re
from types import TracebackType

import pytest
from supabase_utils.http.headers import Headers
from supabase_utils.http.io import AsyncHttpIO

# Import the class to test
from supabase_utils.http.request import HTTPRequestMethod, Request, Response
from supabase_utils.types import JSON, JSONParser
from yarl import URL

from supabase_functions.client import AsyncFunctionsClient, FunctionsClient
from supabase_functions.errors import FunctionsHttpError, FunctionsRelayError
from supabase_functions.utils import FunctionRegion
from supabase_functions.version import __version__


def client_returning(
    content: bytes,
    status: int,
    headers: Headers | None = None,
    client_headers: dict[str, str] | None = None,
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
        headers=client_headers or {},
        executor=AsyncHttpIO(session=MockHttpClient()),
    )


async def test_init_with_valid_params() -> None:
    client = AsyncFunctionsClient(url="https://supabase.com", headers={})
    assert "X-Client-Info" in client.default_headers
    assert re.match(
        rf"^supabase-py/supabase_functions v{re.escape(__version__)}; platform=.+; platform-version=.+; runtime=python; runtime-version=\S+$",
        client.default_headers["X-Client-Info"],
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
    with pytest.raises(FunctionsHttpError, match="Custom error message") as exc_info:
        await client.invoke("test-function")
    assert exc_info.value.status == 400


async def test_invoke_http_error_with_non_json_body() -> None:
    client = client_returning(content=b"not json", status=400)
    with pytest.raises(FunctionsHttpError, match="not json"):
        await client.invoke("test-function")


async def test_invoke_http_error_with_empty_body() -> None:
    client = client_returning(content=b"", status=500)
    with pytest.raises(
        FunctionsHttpError, match="An error occurred while requesting"
    ) as exc_info:
        await client.invoke("test-function")
    assert exc_info.value.status == 500


async def test_invoke_with_relay_error() -> None:
    client = client_returning(
        content=b'{"error": "Relay error message"}',
        status=200,
        headers=Headers.from_mapping({"x-relay-error": "true"}),
    )
    with pytest.raises(FunctionsRelayError, match="Relay error message"):
        await client.invoke("test-function")


async def test_invoke_relay_error_on_non_2xx_status() -> None:
    client = client_returning(
        content=b"relay exploded",
        status=546,
        headers=Headers.from_mapping({"X-Relay-Error": "true"}),
    )
    with pytest.raises(FunctionsRelayError, match="relay exploded") as exc_info:
        await client.invoke("test-function")
    assert not isinstance(exc_info.value, FunctionsHttpError)
    assert exc_info.value.status == 546


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


async def test_invoke_does_not_leak_per_call_headers() -> None:
    client = client_returning(content=b"{}", status=200)
    before = client.default_headers
    first = await client.invoke(
        "test-function",
        body={"key": "value"},
        region=FunctionRegion.UsEast1,
        headers={"x-one-off": "yes"},
    )
    second = await client.invoke("test-function")

    assert first.request.headers["x-one-off"] == "yes"
    assert "x-one-off" not in second.request.headers
    assert "x-region" not in second.request.headers
    assert "Content-Type" not in second.request.headers
    assert client.default_headers is before
    assert "x-one-off" not in client.default_headers
    assert "Content-Type" not in client.default_headers


async def test_invoke_per_call_headers_override_client_headers() -> None:
    client = client_returning(
        content=b"{}",
        status=200,
        client_headers={"authorization": "Bearer valid.jwt.token"},
    )
    response = await client.invoke(
        "test-function", headers={"Authorization": "Bearer override"}
    )
    assert response.request.headers.get_list("Authorization") == ["Bearer override"]
    assert client.default_headers["Authorization"] == "Bearer valid.jwt.token"


@pytest.mark.parametrize("method", ["GET", "PUT", "PATCH", "DELETE"])
async def test_invoke_with_method(method: HTTPRequestMethod) -> None:
    client = client_returning(content=b"{}", status=200)
    response = await client.invoke("test-function", method=method)
    assert response.request.method == method


async def test_invoke_defaults_to_post() -> None:
    client = client_returning(content=b"{}", status=200)
    response = await client.invoke("test-function")
    assert response.request.method == "POST"


async def test_invoke_with_bytes_body() -> None:
    client = client_returning(content=b"{}", status=200)
    response = await client.invoke("test-function", body=b"\x00binary")
    assert response.request.headers["Content-Type"] == "application/octet-stream"
    assert response.request.content == b"\x00binary"


async def test_invoke_string_body_sent_as_content() -> None:
    client = client_returning(content=b"{}", status=200)
    response = await client.invoke("test-function", body="string data")
    assert response.request.content == b"string data"


@pytest.mark.parametrize(
    "body", ["<xml/>", {"key": "value"}, b"<xml/>"], ids=["str", "dict", "bytes"]
)
@pytest.mark.parametrize("header_name", ["Content-Type", "content-type"])
async def test_invoke_does_not_overwrite_content_type(
    body: bytes | str | dict[str, JSON], header_name: str
) -> None:
    client = client_returning(content=b"{}", status=200)
    response = await client.invoke(
        "test-function", body=body, headers={header_name: "application/xml"}
    )
    assert response.request.headers.get_list("Content-Type") == ["application/xml"]


async def test_invoke_does_not_overwrite_client_content_type() -> None:
    client = client_returning(
        content=b"{}",
        status=200,
        client_headers={"Content-Type": "application/xml"},
    )
    response = await client.invoke("test-function", body="<xml/>")
    assert response.request.headers.get_list("Content-Type") == ["application/xml"]


@pytest.mark.parametrize("body", [[1, 2, 3], []], ids=["list", "empty-list"])
async def test_invoke_with_list_body_sends_json(body: list[JSON]) -> None:
    client = client_returning(content=b"{}", status=200)
    response = await client.invoke("test-function", body=body)
    assert response.request.headers["Content-Type"] == "application/json"
    assert response.request.content == JSONParser.dump_json(body)


async def test_invoke_with_bytearray_body() -> None:
    client = client_returning(content=b"{}", status=200)
    response = await client.invoke("test-function", body=bytearray(b"x"))  # type: ignore[arg-type]
    assert response.request.content == b"x"


async def test_invoke_with_unsupported_body_raises() -> None:
    client = client_returning(content=b"{}", status=200)
    with pytest.raises(TypeError):
        await client.invoke("test-function", body=1.5)  # type: ignore[arg-type]


async def test_invoke_raises_on_300() -> None:
    client = client_returning(content=b"", status=300)
    with pytest.raises(FunctionsHttpError):
        await client.invoke("test-function")
