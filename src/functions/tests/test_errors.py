from typing import Type

import pytest

from supabase_functions.errors import (
    FunctionsApiErrorDict,
    FunctionsError,
    FunctionsHttpError,
    FunctionsRelayError,
)


@pytest.mark.parametrize(
    "error_class,expected_name,expected_status",
    [
        (FunctionsError, "test_error", 500),
        (FunctionsHttpError, "FunctionsHttpError", 400),
        (FunctionsRelayError, "FunctionsRelayError", 400),
    ],
)
def test_error_initialization(
    error_class: Type[FunctionsError], expected_name: str, expected_status: int
):
    test_message = "Test error message"
    if issubclass(error_class, (FunctionsHttpError, FunctionsRelayError)):
        error: FunctionsError = error_class(test_message)
    elif error_class is FunctionsError:
        error = error_class(test_message, expected_name, expected_status)

    assert str(error) == test_message
    assert error.message == test_message
    assert error.name == expected_name
    assert error.status == expected_status
    assert isinstance(error, Exception)


@pytest.mark.parametrize(
    "error_class,expected_name,expected_status",
    [
        (FunctionsError, "test_error", 500),
        (FunctionsHttpError, "FunctionsHttpError", 400),
        (FunctionsRelayError, "FunctionsRelayError", 400),
    ],
)
def test_error_to_dict(
    error_class: Type[FunctionsError], expected_name: str, expected_status: int
):
    test_message = "Test error message"

    if issubclass(error_class, (FunctionsHttpError, FunctionsRelayError)):
        error: FunctionsError = error_class(test_message)
    elif error_class is FunctionsError:
        error = error_class(test_message, expected_name, expected_status)

    error_dict = error.to_dict()

    assert isinstance(error_dict, dict)
    assert error_dict["message"] == test_message
    assert error_dict["name"] == expected_name
    assert error_dict["status"] == expected_status

    # Verify the dict matches the TypedDict structure
    typed_dict: FunctionsApiErrorDict = error_dict
    assert isinstance(typed_dict["name"], str)
    assert isinstance(typed_dict["message"], str)
    assert isinstance(typed_dict["status"], int)


def test_functions_error_inheritance():
    # Test that all error classes inherit from FunctionsError
    assert issubclass(FunctionsHttpError, FunctionsError)
    assert issubclass(FunctionsRelayError, FunctionsError)


def test_error_as_exception():
    # Test that errors can be raised and caught
    test_message = "Test exception"

    # Test base error
    with pytest.raises(FunctionsError) as exc_info:
        raise FunctionsError(test_message, "test_error", 500)
    assert str(exc_info.value) == test_message

    # Test HTTP error
    with pytest.raises(FunctionsHttpError) as exc_info:
        raise FunctionsHttpError(test_message)
    assert str(exc_info.value) == test_message

    # Test Relay error
    with pytest.raises(FunctionsRelayError) as exc_info:
        raise FunctionsRelayError(test_message)
    assert str(exc_info.value) == test_message


def test_error_message_types():
    # Test that errors handle different message types appropriately
    test_cases = [
        "Simple string",
        "String with unicode: 你好",
        "String with special chars: !@#$%^&*()",
        "",  # Empty string
        "A" * 1000,  # Long string
    ]

    for message in test_cases:
        error = FunctionsError(message, "test", 500)
        assert error.message == message
        assert error.to_dict()["message"] == message
