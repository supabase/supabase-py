import sys
from typing import Any

import pytest

from supabase_functions.utils import (
    FunctionRegion,
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


@pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason="StrEnum import test only relevant for Python 3.11+",
)
def test_strenum_import_python_311_plus() -> None:
    from enum import StrEnum as BuiltinStrEnum  # type: ignore

    assert isinstance(FunctionRegion.Any, BuiltinStrEnum)


@pytest.mark.skipif(
    sys.version_info >= (3, 11),
    reason="strenum import test only relevant for Python < 3.11",
)
def test_strenum_import_python_310_and_below() -> None:
    from strenum import StrEnum as ExternalStrEnum

    assert isinstance(FunctionRegion.Any, ExternalStrEnum)
