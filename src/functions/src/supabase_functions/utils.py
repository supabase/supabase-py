import sys
from typing import Dict, Optional, Union

from httpx import AsyncClient as AsyncClient  # noqa: F401
from pydantic import BaseModel, Field
from supabase_utils.http import HTTPRequestMethod
from supabase_utils.types import JSON

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from strenum import StrEnum


DEFAULT_FUNCTION_CLIENT_TIMEOUT = 5


class FunctionRegion(StrEnum):
    Any = "any"
    ApNortheast1 = "ap-northeast-1"
    ApNortheast2 = "ap-northeast-2"
    ApSouth1 = "ap-south-1"
    ApSoutheast1 = "ap-southeast-1"
    ApSoutheast2 = "ap-southeast-2"
    CaCentral1 = "ca-central-1"
    EuCentral1 = "eu-central-1"
    EuWest1 = "eu-west-1"
    EuWest2 = "eu-west-2"
    EuWest3 = "eu-west-3"
    SaEast1 = "sa-east-1"
    UsEast1 = "us-east-1"
    UsWest1 = "us-west-1"
    UsWest2 = "us-west-2"


class InvokeOptions(BaseModel):
    body: Union[bytes, str, Dict[str, JSON], None] = None
    region: Optional[FunctionRegion] = None
    headers: Dict[str, str] = Field(default_factory=dict)
    response_type: Optional[str] = None
    method: Optional[HTTPRequestMethod] = None


def is_valid_str_arg(target: str) -> bool:
    return isinstance(target, str) and len(target.strip()) > 0
