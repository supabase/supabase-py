import pickle

import pytest
from supabase_utils.errors import SupabaseError

from realtime import (
    AuthorizationError,
    MaxRetriesExceeded,
    NotConnectedError,
    RealtimeError,
)


def test_realtime_errors_inherit_the_shared_root() -> None:
    assert issubclass(RealtimeError, SupabaseError)
    for error_class in (AuthorizationError, MaxRetriesExceeded, NotConnectedError):
        assert issubclass(error_class, RealtimeError)


def test_not_connected_error_names_the_method() -> None:
    error = NotConnectedError("send")
    assert error.offending_func_name == "send"
    assert "AsyncRealtimeClient.send()" in str(error)
    assert str(error) == error.message


def test_authorization_error_has_a_default_message() -> None:
    assert str(AuthorizationError()) == "Authorization failed for private channel"
    assert str(AuthorizationError("nope")) == "nope"


def test_max_retries_exceeded_keeps_the_count() -> None:
    error = MaxRetriesExceeded(3)
    assert error.retries == 3
    assert str(error) == "Reconnecting failed after 3 attempts"
    with pytest.raises(SupabaseError):
        raise error


def test_errors_can_be_pickled() -> None:
    clone = pickle.loads(pickle.dumps(NotConnectedError("send")))
    assert isinstance(clone, NotConnectedError)
    assert clone.offending_func_name == "send"
    assert str(clone) == str(NotConnectedError("send"))
