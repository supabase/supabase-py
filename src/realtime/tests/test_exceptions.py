import pickle

import pytest
from supabase_utils.errors import SupabaseError

from realtime import (
    AuthorizationError,
    ChannelJoinError,
    NotConnectedError,
    RealtimeError,
    RealtimeTimeoutError,
)
from realtime.exceptions import _is_fatal, _join_error


def test_realtime_errors_inherit_the_shared_root() -> None:
    assert issubclass(RealtimeError, SupabaseError)
    for error_class in (
        AuthorizationError,
        ChannelJoinError,
        NotConnectedError,
        RealtimeTimeoutError,
    ):
        assert issubclass(error_class, RealtimeError)
    assert issubclass(AuthorizationError, ChannelJoinError)
    assert issubclass(RealtimeTimeoutError, TimeoutError)


def test_not_connected_error_names_the_method() -> None:
    error = NotConnectedError("send")
    assert error.offending_func_name == "send"
    assert "calling send()" in str(error)
    assert str(error) == error.message


def test_not_connected_error_takes_a_message() -> None:
    error = NotConnectedError("send", "the connection dropped")
    assert error.offending_func_name == "send"
    assert str(error) == "the connection dropped"


def test_timeout_error_names_the_push() -> None:
    error = RealtimeTimeoutError("phx_join", "realtime:room", 2.5)
    assert (error.event, error.topic, error.timeout) == (
        "phx_join",
        "realtime:room",
        2.5,
    )
    assert str(error) == (
        "the server did not reply to phx_join on 'realtime:room' within 2.5 seconds"
    )


@pytest.mark.parametrize(
    ("reason", "error_class", "code"),
    [
        (
            "Unauthorized: You do not have permissions",
            AuthorizationError,
            "Unauthorized",
        ),
        (
            "InvalidJWTToken: Token has expired 5 seconds ago",
            AuthorizationError,
            "InvalidJWTToken",
        ),
        ("MalformedJWT: The token is malformed", AuthorizationError, "MalformedJWT"),
        (
            "ChannelRateLimitReached: Too many channels",
            ChannelJoinError,
            "ChannelRateLimitReached",
        ),
        (
            "PrivateOnly: This project only allows private channels",
            ChannelJoinError,
            "PrivateOnly",
        ),
        ("Unknown Error on Channel", ChannelJoinError, None),
        ("Realtime was unable to connect: try again", ChannelJoinError, None),
    ],
)
def test_join_errors_are_classified_by_the_code_of_the_reason(
    reason: str, error_class: type[ChannelJoinError], code: str | None
) -> None:
    error = _join_error("realtime:room", reason)
    assert type(error) is error_class
    assert error.reason == reason
    assert error.code == code
    assert error.topic == "realtime:room"
    assert reason in str(error)


@pytest.mark.parametrize(
    ("error", "fatal"),
    [
        (_join_error("t", "Unauthorized: denied"), True),
        (_join_error("t", "PrivateOnly: only private"), True),
        (_join_error("t", "TenantNotFound: missing"), True),
        (_join_error("t", "ChannelRateLimitReached: Too many channels"), False),
        (_join_error("t", "Unknown Error on Channel"), False),
        (RealtimeTimeoutError("phx_join", "t", 1), False),
        (NotConnectedError("subscribe"), False),
        (RealtimeError("mismatch between server and client bindings"), True),
        (OSError("token callback failed"), False),
    ],
)
def test_only_errors_a_retry_cannot_fix_are_fatal(
    error: Exception, fatal: bool
) -> None:
    assert _is_fatal(error) is fatal


def test_errors_can_be_pickled() -> None:
    clone = pickle.loads(pickle.dumps(NotConnectedError("send")))
    assert isinstance(clone, NotConnectedError)
    assert clone.offending_func_name == "send"
    assert str(clone) == str(NotConnectedError("send"))

    join_error = pickle.loads(pickle.dumps(_join_error("t", "Unauthorized: denied")))
    assert isinstance(join_error, AuthorizationError)
    assert (join_error.reason, join_error.code) == (
        "Unauthorized: denied",
        "Unauthorized",
    )

    timeout = pickle.loads(
        pickle.dumps(RealtimeTimeoutError("heartbeat", "phoenix", 5))
    )
    assert isinstance(timeout, RealtimeTimeoutError)
    assert timeout.timeout == 5
