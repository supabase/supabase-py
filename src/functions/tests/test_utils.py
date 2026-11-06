from enum import StrEnum
from typing import Any

import pytest

from supabase_functions.utils import (
    FunctionRegion,
    is_valid_string_argument,
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
    ("test_input", "expected"),
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
def test_is_valid_string_argument(test_input: Any, expected: bool) -> None:
    assert is_valid_string_argument(test_input) == expected


def test_function_region_is_str_enum() -> None:
    assert isinstance(FunctionRegion.Any, StrEnum)
