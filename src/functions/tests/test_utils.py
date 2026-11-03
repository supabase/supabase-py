from typing import Any

import pytest
from supabase_functions.utils import (
    BASE64URL_REGEX,
    FunctionRegion,
    is_http_url,
    is_valid_str_arg,
)


def test_function_region_values() -> None:
    assert FunctionRegion.Any.value == "any"
    assert FunctionRegion.ApNortheast1.value == "ap-northeast-1"
    assert FunctionRegion.ApNortheast2.value == "ap-northeast-2"
    assert FunctionRegion.ApSouth1.value == "ap-south-1"
    assert FunctionRegion.ApSoutheast1.value == "ap-southeast-1"
    assert FunctionRegion.ApSoutheast2.value == "ap-southeast-2"
    assert FunctionRegion.CaCentral1.value == "ca-central-1"
    assert FunctionRegion.EuCentral1.value == "eu-central-1"
    assert FunctionRegion.EuWest1.value == "eu-west-1"
    assert FunctionRegion.EuWest2.value == "eu-west-2"
    assert FunctionRegion.EuWest3.value == "eu-west-3"
    assert FunctionRegion.SaEast1.value == "sa-east-1"
    assert FunctionRegion.UsEast1.value == "us-east-1"
    assert FunctionRegion.UsWest1.value == "us-west-1"
    assert FunctionRegion.UsWest2.value == "us-west-2"


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("valid_string", True),
        ("  spaced_string  ", True),
        ("", False),
        ("   ", False),
        (None, False),
        (123, False),
        ([], False),
        ({}, False),
    ],
)
def test_is_valid_str_arg(test_input: Any, expected: bool) -> None:
    assert is_valid_str_arg(test_input) == expected


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("https://example.com", True),
        ("http://localhost", True),
        ("http://127.0.0.1:8000", True),
        ("https://api.supabase.com", True),
        ("ftp://example.com", False),
        ("ws://example.com", False),
        ("not-a-url", False),
        ("", False),
    ],
)
def test_is_http_url(test_input: str, expected: bool) -> None:
    assert is_http_url(test_input) == expected


def test_base64url_regex() -> None:
    import re

    pattern = re.compile(BASE64URL_REGEX, re.IGNORECASE)

    # Valid base64url strings
    assert pattern.match("abcd")
    assert pattern.match("1234")
    assert pattern.match("abc")
    assert pattern.match("12")
    assert pattern.match("ab")
    assert pattern.match("ABCD")
    assert pattern.match("ABC")
    assert pattern.match("AB")
    assert pattern.match("a-b_")

    # Invalid base64url strings
    assert not pattern.match("a")  # too short
    assert not pattern.match("abcde")  # invalid length
    assert not pattern.match("abc!")  # invalid character
    assert not pattern.match("abc@")  # invalid character


def test_function_region_is_builtin_strenum() -> None:
    from enum import StrEnum

    assert isinstance(FunctionRegion.Any, StrEnum)
