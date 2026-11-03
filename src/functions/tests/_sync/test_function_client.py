import re
from unittest.mock import Mock, patch

import pytest
from httpx import Client, HTTPError, MockTransport, Request, Response, Timeout

# Import the class to test
from supabase_functions import SyncFunctionsClient
from supabase_functions.errors import FunctionsHttpError, FunctionsRelayError
from supabase_functions.utils import FunctionRegion
from supabase_functions.version import __version__


@pytest.fixture
def valid_url() -> str:
    return "https://example.com"


@pytest.fixture
def default_headers() -> dict[str, str]:
    return {"Authorization": "Bearer valid.jwt.token"}


@pytest.fixture
def client(valid_url: str, default_headers: dict[str, str]) -> SyncFunctionsClient:
    return SyncFunctionsClient(
        url=valid_url, headers=default_headers, timeout=10, verify=True
    )


def test_init_with_valid_params(
    valid_url: str, default_headers: dict[str, str]
) -> None:
    client = SyncFunctionsClient(
        url=valid_url, headers=default_headers, timeout=10, verify=True
    )
    assert str(client.url) == valid_url
    assert "X-Client-Info" in client.headers
    assert re.match(
        rf"^supabase-py/supabase_functions v{re.escape(__version__)}; platform=.+; platform-version=.+; runtime=python; runtime-version=\S+$",
        client.headers["X-Client-Info"],
    )
    assert client._client.timeout == Timeout(10)


@pytest.mark.parametrize("invalid_url", ["not-a-url", "ftp://invalid.com", "", None])
def test_init_with_invalid_url(
    invalid_url: str, default_headers: dict[str, str]
) -> None:
    with pytest.raises(ValueError, match="url must be a valid HTTP URL string"):
        SyncFunctionsClient(url=invalid_url, headers=default_headers, timeout=10)


def test_set_auth_valid_token(client: SyncFunctionsClient) -> None:
    valid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
    client.set_auth(valid_token)
    assert client.headers["Authorization"] == f"Bearer {valid_token}"


def test_invoke_success_json(client: SyncFunctionsClient) -> None:
    mock_response = Mock(spec=Response)
    mock_response.json.return_value = {"message": "success"}
    mock_response.raise_for_status = Mock()
    mock_response.headers = {}

    with patch.object(client._client, "request", new_callable=Mock) as mock_request:
        mock_request.return_value = mock_response

        result = client.invoke(
            "test-function", {"responseType": "json", "body": {"test": "data"}}
        )

        assert result == {"message": "success"}
        mock_request.assert_called_once()
        _, kwargs = mock_request.call_args
        assert kwargs["json"] == {"test": "data"}


def test_invoke_success_binary(client: SyncFunctionsClient) -> None:
    mock_response = Mock(spec=Response)
    mock_response.content = b"binary content"
    mock_response.raise_for_status = Mock()
    mock_response.headers = {}

    with patch.object(client._client, "request", new_callable=Mock) as mock_request:
        mock_request.return_value = mock_response

        result = client.invoke("test-function")

        assert result == b"binary content"
        mock_request.assert_called_once()


def test_invoke_does_not_leak_headers_between_calls(
    client: SyncFunctionsClient,
) -> None:
    # invoke() must not mutate the client's persistent headers: a per-call
    # header and the body Content-Type must not bleed into later calls.
    before = dict(client.headers)

    mock_response = Mock(spec=Response)
    mock_response.json.return_value = {}
    mock_response.content = b""
    mock_response.raise_for_status = Mock()
    mock_response.headers = {}

    with patch.object(client._client, "request", new_callable=Mock) as mock_request:
        mock_request.return_value = mock_response

        client.invoke("fn1", {"body": {"a": 1}, "headers": {"X-Once": "1"}})

    assert dict(client.headers) == before
    assert "X-Once" not in client.headers
    assert "Content-Type" not in client.headers


def test_invoke_with_region(client: SyncFunctionsClient) -> None:
    mock_response = Mock(spec=Response)
    mock_response.json.return_value = {"message": "success"}
    mock_response.raise_for_status = Mock()
    mock_response.headers = {}

    with patch.object(client._client, "request", new_callable=Mock) as mock_request:
        mock_request.return_value = mock_response

        client.invoke("test-function", {"region": FunctionRegion("us-east-1")})

        args, kwargs = mock_request.call_args
        # Check that x-region header is present
        assert kwargs["headers"]["x-region"] == "us-east-1"
        # Check that the URL contains the forceFunctionRegion query parameter
        assert kwargs["params"]["forceFunctionRegion"] == "us-east-1"


def test_invoke_with_region_string(client: SyncFunctionsClient) -> None:
    mock_response = Mock(spec=Response)
    mock_response.json.return_value = {"message": "success"}
    mock_response.raise_for_status = Mock()
    mock_response.headers = {}

    with patch.object(client._client, "request", new_callable=Mock) as mock_request:
        mock_request.return_value = mock_response

        with pytest.warns(UserWarning, match=r"Use FunctionRegion\(us-east-1\)"):
            client.invoke("test-function", {"region": "us-east-1"})

        args, kwargs = mock_request.call_args
        # Check that x-region header is present
        assert kwargs["headers"]["x-region"] == "us-east-1"
        # Check that the URL contains the forceFunctionRegion query parameter
        assert kwargs["params"]["forceFunctionRegion"] == "us-east-1"


def test_invoke_with_http_error(client: SyncFunctionsClient) -> None:
    mock_response = Mock(spec=Response)
    mock_response.json.return_value = {"error": "Custom error message"}
    mock_response.raise_for_status.side_effect = HTTPError("HTTP Error")
    mock_response.headers = {}

    with patch.object(client._client, "request", new_callable=Mock) as mock_request:
        mock_request.return_value = mock_response

        with pytest.raises(FunctionsHttpError, match="Custom error message"):
            client.invoke("test-function")


def test_invoke_with_relay_error(client: SyncFunctionsClient) -> None:
    mock_response = Mock(spec=Response)
    mock_response.text = '{"error": "Relay error message"}'
    mock_response.status_code = 200
    mock_response.raise_for_status = Mock()
    mock_response.headers = {"x-relay-error": "true"}

    with patch.object(client._client, "request", new_callable=Mock) as mock_request:
        mock_request.return_value = mock_response

        with pytest.raises(FunctionsRelayError, match="Relay error message"):
            client.invoke("test-function")


def test_invoke_relay_error_on_non_2xx_status(
    client: SyncFunctionsClient,
) -> None:
    mock_response = Mock(spec=Response)
    mock_response.text = '{"error": "Relay error message"}'
    mock_response.status_code = 546
    mock_response.raise_for_status.side_effect = HTTPError("HTTP Error")
    mock_response.headers = {"x-relay-error": "true"}

    with patch.object(client._client, "request", new_callable=Mock) as mock_request:
        mock_request.return_value = mock_response

        with pytest.raises(
            FunctionsRelayError, match="Relay error message"
        ) as exc_info:
            client.invoke("test-function")

    assert not isinstance(exc_info.value, FunctionsHttpError)
    assert exc_info.value.status == 546


def test_invoke_invalid_function_name(client: SyncFunctionsClient) -> None:
    with pytest.raises(ValueError, match="function_name must a valid string value."):
        client.invoke("")


def test_invoke_with_string_body(client: SyncFunctionsClient) -> None:
    mock_response = Mock(spec=Response)
    mock_response.json.return_value = {"message": "success"}
    mock_response.raise_for_status = Mock()
    mock_response.headers = {}

    with patch.object(client._client, "request", new_callable=Mock) as mock_request:
        mock_request.return_value = mock_response

        client.invoke("test-function", {"body": "string data"})

        _, kwargs = mock_request.call_args
        assert kwargs["headers"]["Content-Type"] == "text/plain"


def test_invoke_with_json_body(client: SyncFunctionsClient) -> None:
    mock_response = Mock(spec=Response)
    mock_response.json.return_value = {"message": "success"}
    mock_response.raise_for_status = Mock()
    mock_response.headers = {}

    with patch.object(client._client, "request", new_callable=Mock) as mock_request:
        mock_request.return_value = mock_response

        client.invoke("test-function", {"body": {"key": "value"}})

        _, kwargs = mock_request.call_args
        assert kwargs["headers"]["Content-Type"] == "application/json"


def test_init_with_httpx_client() -> None:
    # Create a custom httpx client with specific options
    headers = {"x-user-agent": "my-app/0.0.1"}
    custom_client = Client(
        timeout=Timeout(30), follow_redirects=True, max_redirects=5, headers=headers
    )

    # Initialize the functions client with the custom httpx client
    client = SyncFunctionsClient(
        url="https://example.com",
        headers={"Authorization": "Bearer token"},
        timeout=10,
        http_client=custom_client,
    )

    # Verify the custom client options are preserved
    assert client._client.timeout == Timeout(30)
    assert client._client.follow_redirects is True
    assert client._client.max_redirects == 5
    assert client._client.headers.get("x-user-agent") == "my-app/0.0.1"

    # Verify the client is properly configured with our custom client
    assert client._client is custom_client


def test_invoke_does_not_leak_per_call_headers(
    client: SyncFunctionsClient,
) -> None:
    mock_response = Mock(spec=Response)
    mock_response.json.return_value = {"message": "success"}
    mock_response.raise_for_status = Mock()
    mock_response.headers = {}

    with patch.object(client._client, "request", new_callable=Mock) as mock_request:
        mock_request.return_value = mock_response

        client.invoke(
            "test-function",
            {
                "headers": {"x-one-off": "yes"},
                "region": FunctionRegion("us-east-1"),
                "body": {"key": "value"},
            },
        )
        client.invoke("test-function")

        first, second = mock_request.call_args_list
        assert first.kwargs["headers"]["x-one-off"] == "yes"
        assert "x-one-off" not in second.kwargs["headers"]
        assert "x-region" not in second.kwargs["headers"]
        assert "Content-Type" not in second.kwargs["headers"]
        assert "x-one-off" not in client.headers


def test_invoke_per_call_headers_override_client_headers(
    client: SyncFunctionsClient,
) -> None:
    mock_response = Mock(spec=Response)
    mock_response.json.return_value = {"message": "success"}
    mock_response.raise_for_status = Mock()
    mock_response.headers = {}

    with patch.object(client._client, "request", new_callable=Mock) as mock_request:
        mock_request.return_value = mock_response

        client.invoke(
            "test-function", {"headers": {"Authorization": "Bearer override"}}
        )

        _, kwargs = mock_request.call_args
        assert kwargs["headers"]["Authorization"] == "Bearer override"
        assert client.headers["Authorization"] == "Bearer valid.jwt.token"


@pytest.mark.parametrize("method", ["GET", "PUT", "PATCH", "DELETE"])
def test_invoke_with_method(client: SyncFunctionsClient, method: str) -> None:
    mock_response = Mock(spec=Response)
    mock_response.json.return_value = {"message": "success"}
    mock_response.raise_for_status = Mock()
    mock_response.headers = {}

    with patch.object(client._client, "request", new_callable=Mock) as mock_request:
        mock_request.return_value = mock_response

        client.invoke("test-function", {"method": method})

        args, _ = mock_request.call_args
        assert args[0] == method


def test_invoke_defaults_to_post(client: SyncFunctionsClient) -> None:
    mock_response = Mock(spec=Response)
    mock_response.json.return_value = {"message": "success"}
    mock_response.raise_for_status = Mock()
    mock_response.headers = {}

    with patch.object(client._client, "request", new_callable=Mock) as mock_request:
        mock_request.return_value = mock_response

        client.invoke("test-function")

        args, _ = mock_request.call_args
        assert args[0] == "POST"


def test_invoke_with_bytes_body(client: SyncFunctionsClient) -> None:
    mock_response = Mock(spec=Response)
    mock_response.json.return_value = {"message": "success"}
    mock_response.raise_for_status = Mock()
    mock_response.headers = {}

    with patch.object(client._client, "request", new_callable=Mock) as mock_request:
        mock_request.return_value = mock_response

        client.invoke("test-function", {"body": b"\x00binary"})

        _, kwargs = mock_request.call_args
        assert kwargs["headers"]["Content-Type"] == "application/octet-stream"
        assert kwargs["content"] == b"\x00binary"


def test_invoke_string_body_sent_as_content(
    client: SyncFunctionsClient,
) -> None:
    mock_response = Mock(spec=Response)
    mock_response.json.return_value = {"message": "success"}
    mock_response.raise_for_status = Mock()
    mock_response.headers = {}

    with patch.object(client._client, "request", new_callable=Mock) as mock_request:
        mock_request.return_value = mock_response

        client.invoke("test-function", {"body": "string data"})

        _, kwargs = mock_request.call_args
        assert kwargs["content"] == "string data"


def test_invoke_http_error_with_non_json_body(
    client: SyncFunctionsClient,
) -> None:
    mock_response = Mock(spec=Response)
    mock_response.text = "boom"
    mock_response.raise_for_status.side_effect = HTTPError("HTTP Error")
    mock_response.headers = {}

    with patch.object(client._client, "request", new_callable=Mock) as mock_request:
        mock_request.return_value = mock_response

        with pytest.raises(FunctionsHttpError, match="boom"):
            client.invoke("test-function")


def test_invoke_http_error_with_empty_body(client: SyncFunctionsClient) -> None:
    error = HTTPError("HTTP Error")
    error.request = Request("POST", "https://example.com/test-function")

    mock_response = Mock(spec=Response)
    mock_response.text = "not json"
    mock_response.raise_for_status.side_effect = error
    mock_response.status_code = 400
    mock_response.headers = {}

    with patch.object(client._client, "request", new_callable=Mock) as mock_request:
        mock_request.return_value = mock_response

        with pytest.raises(FunctionsHttpError, match="not json"):
            client.invoke("test-function")


def _recording_client(seen: list[Request]) -> SyncFunctionsClient:
    def handler(request: Request) -> Response:
        seen.append(request)
        return Response(200, content=b"ok")

    return SyncFunctionsClient(
        url="https://example.com/functions/v1",
        headers={},
        http_client=Client(transport=MockTransport(handler)),
    )


@pytest.mark.parametrize("function_name", ["hello?name=bob", "hello?name=bob#top"])
def test_invoke_keeps_query_string_in_function_name(function_name: str) -> None:
    seen: list[Request] = []
    client = _recording_client(seen)

    client.invoke(function_name, {"region": FunctionRegion.UsEast1})

    (request,) = seen
    assert request.url.path == "/functions/v1/hello", str(request.url)
    assert dict(request.url.params) == {
        "name": "bob",
        "forceFunctionRegion": "us-east-1",
    }


def test_invoke_plain_function_name_has_no_query() -> None:
    seen: list[Request] = []
    client = _recording_client(seen)

    client.invoke("hello")

    (request,) = seen
    assert request.url.path == "/functions/v1/hello"
    assert request.url.query == b""


@pytest.mark.parametrize("function_name", ["?name=bob", "#top", " ?a=1"])
def test_invoke_rejects_name_without_path(function_name: str) -> None:
    seen: list[Request] = []
    client = _recording_client(seen)

    with pytest.raises(ValueError):
        client.invoke(function_name)

    assert seen == []


def test_invoke_query_string_keeps_repeated_and_encoded_values() -> None:
    seen: list[Request] = []
    client = _recording_client(seen)

    client.invoke("dir/fn?a=1&a=2&q=a%20b&p=x%2By")

    (request,) = seen
    assert request.url.path == "/functions/v1/dir/fn"
    assert request.url.params.multi_items() == [
        ("a", "1"),
        ("a", "2"),
        ("q", "a b"),
        ("p", "x+y"),
    ]
