from unittest.mock import AsyncMock, Mock, patch

import pytest
from httpx import AsyncClient, HTTPError, Response, Timeout

# Import the class to test
from supabase_functions import AsyncFunctionsClient
from supabase_functions.errors import FunctionsHttpError, FunctionsRelayError
from supabase_functions.utils import FunctionRegion
from supabase_functions.version import __version__


@pytest.fixture
def valid_url():
    return "https://example.com"


@pytest.fixture
def default_headers():
    return {"Authorization": "Bearer valid.jwt.token"}


@pytest.fixture
def client(valid_url, default_headers):
    return AsyncFunctionsClient(
        url=valid_url, headers=default_headers, timeout=10, verify=True
    )


async def test_init_with_valid_params(valid_url, default_headers):
    client = AsyncFunctionsClient(
        url=valid_url, headers=default_headers, timeout=10, verify=True
    )
    assert str(client.url) == valid_url
    assert "User-Agent" in client.headers
    assert client.headers["User-Agent"] == f"supabase-py/functions-py v{__version__}"
    assert client._client.timeout == Timeout(10)


@pytest.mark.parametrize("invalid_url", ["not-a-url", "ftp://invalid.com", "", None])
def test_init_with_invalid_url(invalid_url, default_headers):
    with pytest.raises(ValueError, match="url must be a valid HTTP URL string"):
        AsyncFunctionsClient(url=invalid_url, headers=default_headers, timeout=10)


async def test_set_auth_valid_token(client: AsyncFunctionsClient):
    valid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
    client.set_auth(valid_token)
    assert client.headers["Authorization"] == f"Bearer {valid_token}"


async def test_invoke_success_json(client: AsyncFunctionsClient):
    mock_response = Mock(spec=Response)
    mock_response.json.return_value = {"message": "success"}
    mock_response.raise_for_status = Mock()
    mock_response.headers = {}

    with patch.object(
        client._client, "request", new_callable=AsyncMock
    ) as mock_request:
        mock_request.return_value = mock_response

        result = await client.invoke(
            "test-function", {"responseType": "json", "body": {"test": "data"}}
        )

        assert result == {"message": "success"}
        mock_request.assert_called_once()
        _, kwargs = mock_request.call_args
        assert kwargs["json"] == {"test": "data"}


async def test_invoke_success_binary(client: AsyncFunctionsClient):
    mock_response = Mock(spec=Response)
    mock_response.content = b"binary content"
    mock_response.raise_for_status = Mock()
    mock_response.headers = {}

    with patch.object(
        client._client, "request", new_callable=AsyncMock
    ) as mock_request:
        mock_request.return_value = mock_response

        result = await client.invoke("test-function")

        assert result == b"binary content"
        mock_request.assert_called_once()


async def test_invoke_with_region(client: AsyncFunctionsClient):
    mock_response = Mock(spec=Response)
    mock_response.json.return_value = {"message": "success"}
    mock_response.raise_for_status = Mock()
    mock_response.headers = {}

    with patch.object(
        client._client, "request", new_callable=AsyncMock
    ) as mock_request:
        mock_request.return_value = mock_response

        await client.invoke("test-function", {"region": FunctionRegion("us-east-1")})

        args, kwargs = mock_request.call_args
        # Check that x-region header is present
        assert kwargs["headers"]["x-region"] == "us-east-1"
        # Check that the URL contains the forceFunctionRegion query parameter
        assert kwargs["params"]["forceFunctionRegion"] == "us-east-1"


async def test_invoke_with_region_string(client: AsyncFunctionsClient):
    mock_response = Mock(spec=Response)
    mock_response.json.return_value = {"message": "success"}
    mock_response.raise_for_status = Mock()
    mock_response.headers = {}

    with patch.object(
        client._client, "request", new_callable=AsyncMock
    ) as mock_request:
        mock_request.return_value = mock_response

        with pytest.warns(UserWarning, match=r"Use FunctionRegion\(us-east-1\)"):
            await client.invoke("test-function", {"region": "us-east-1"})

        args, kwargs = mock_request.call_args
        # Check that x-region header is present
        assert kwargs["headers"]["x-region"] == "us-east-1"
        # Check that the URL contains the forceFunctionRegion query parameter
        assert kwargs["params"]["forceFunctionRegion"] == "us-east-1"


async def test_invoke_with_http_error(client: AsyncFunctionsClient):
    mock_response = Mock(spec=Response)
    mock_response.json.return_value = {"error": "Custom error message"}
    mock_response.raise_for_status.side_effect = HTTPError("HTTP Error")
    mock_response.headers = {}

    with patch.object(
        client._client, "request", new_callable=AsyncMock
    ) as mock_request:
        mock_request.return_value = mock_response

        with pytest.raises(FunctionsHttpError, match="Custom error message"):
            await client.invoke("test-function")


async def test_invoke_with_relay_error(client: AsyncFunctionsClient):
    mock_response = Mock(spec=Response)
    mock_response.json.return_value = {"error": "Relay error message"}
    mock_response.raise_for_status = Mock()
    mock_response.headers = {"x-relay-header": "true"}

    with patch.object(
        client._client, "request", new_callable=AsyncMock
    ) as mock_request:
        mock_request.return_value = mock_response

        with pytest.raises(FunctionsRelayError, match="Relay error message"):
            await client.invoke("test-function")


async def test_invoke_invalid_function_name(client: AsyncFunctionsClient):
    with pytest.raises(ValueError, match="function_name must a valid string value."):
        await client.invoke("")


async def test_invoke_with_string_body(client: AsyncFunctionsClient):
    mock_response = Mock(spec=Response)
    mock_response.json.return_value = {"message": "success"}
    mock_response.raise_for_status = Mock()
    mock_response.headers = {}

    with patch.object(
        client._client, "request", new_callable=AsyncMock
    ) as mock_request:
        mock_request.return_value = mock_response

        await client.invoke("test-function", {"body": "string data"})

        _, kwargs = mock_request.call_args
        assert kwargs["headers"]["Content-Type"] == "text/plain"


async def test_invoke_with_json_body(client: AsyncFunctionsClient):
    mock_response = Mock(spec=Response)
    mock_response.json.return_value = {"message": "success"}
    mock_response.raise_for_status = Mock()
    mock_response.headers = {}

    with patch.object(
        client._client, "request", new_callable=AsyncMock
    ) as mock_request:
        mock_request.return_value = mock_response

        await client.invoke("test-function", {"body": {"key": "value"}})

        _, kwargs = mock_request.call_args
        assert kwargs["headers"]["Content-Type"] == "application/json"


async def test_init_with_httpx_client():
    # Create a custom httpx client with specific options
    headers = {"x-user-agent": "my-app/0.0.1"}
    custom_client = AsyncClient(
        timeout=Timeout(30), follow_redirects=True, max_redirects=5, headers=headers
    )

    # Initialize the functions client with the custom httpx client
    client = AsyncFunctionsClient(
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
