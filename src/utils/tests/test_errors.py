import copy
import pickle

import pytest
from supabase_utils.errors import SupabaseError
from supabase_utils.http.errors import (
    RequestTimeoutError,
    SupabaseAPIError,
    SupabaseTransportError,
)
from supabase_utils.http.headers import Headers
from supabase_utils.http.request import Request, Response
from yarl import URL


def make_request() -> Request:
    return Request(
        url=URL("https://example.com/rest/v1/items?select=id"),
        method="GET",
        headers=Headers.empty(),
        content=None,
        delay=None,
    )


def make_response(status: int = 404) -> Response:
    return Response(
        headers=Headers.from_mapping({"sb-request-id": "req-1"}),
        content=b'{"message":"missing"}',
        status=status,
        request=make_request(),
    )


class CustomError(SupabaseError):
    def __init__(self, value: int) -> None:
        super().__init__(f"custom {value}", code="custom")
        self.value = value


def test_supabase_error_message_and_code() -> None:
    error = SupabaseError("boom")
    assert isinstance(error, Exception)
    assert str(error) == "boom"
    assert error.message == "boom"
    assert error.code is None
    assert SupabaseError("boom", code="PGRST116").code == "PGRST116"


def test_api_error_carries_status_code_and_response() -> None:
    response = make_response()
    error = SupabaseAPIError(
        "missing", status_code=404, code="not_found", response=response
    )
    assert isinstance(error, SupabaseError)
    assert str(error) == "missing"
    assert error.status_code == 404
    assert error.code == "not_found"
    assert error.response is response
    assert error.response.headers.get("sb-request-id") == "req-1"
    assert SupabaseAPIError("x", status_code=500).response is None


def test_transport_error_describes_the_request_without_the_query() -> None:
    error = SupabaseTransportError(make_request())
    assert isinstance(error, SupabaseError)
    assert not isinstance(error, SupabaseAPIError)
    assert str(error) == "GET https://example.com/rest/v1/items failed"
    assert error.request.method == "GET"
    detailed = SupabaseTransportError(make_request(), "failed: connection refused")
    assert str(detailed) == (
        "GET https://example.com/rest/v1/items failed: connection refused"
    )


def test_request_timeout_error_is_a_transport_error_and_a_timeout() -> None:
    error = RequestTimeoutError(make_request())
    assert isinstance(error, SupabaseTransportError)
    assert isinstance(error, TimeoutError)
    assert str(error) == "GET https://example.com/rest/v1/items timed out"


def test_transport_error_can_be_caught_as_supabase_error() -> None:
    with pytest.raises(SupabaseError):
        raise RequestTimeoutError(make_request())


@pytest.mark.parametrize(
    "error",
    [
        SupabaseError("boom", code="c"),
        SupabaseAPIError(
            "missing", status_code=404, code="n", response=make_response()
        ),
        SupabaseTransportError(make_request(), "failed: refused"),
        RequestTimeoutError(make_request()),
        CustomError(7),
    ],
)
def test_errors_can_be_pickled_and_copied(error: SupabaseError) -> None:
    for clone in (pickle.loads(pickle.dumps(error)), copy.copy(error)):
        assert type(clone) is type(error)
        assert str(clone) == str(error)
        assert clone.args == error.args
        assert clone.message == error.message
        assert clone.code == error.code
        for name, value in vars(error).items():
            if isinstance(value, (Request, Response)):
                assert str(getattr(clone, name)) == str(value)
            else:
                assert getattr(clone, name) == value


def test_pickled_api_error_keeps_the_response() -> None:
    error = SupabaseAPIError("missing", status_code=404, response=make_response())
    clone = pickle.loads(pickle.dumps(error))
    assert clone.status_code == 404
    assert clone.response is not None
    assert clone.response.status == 404
    assert clone.response.content == b'{"message":"missing"}'
