import sys
from urllib.parse import urlparse

from httpx import AsyncClient as AsyncClient  # noqa: F401

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from strenum import StrEnum


DEFAULT_FUNCTION_CLIENT_TIMEOUT = 5
BASE64URL_REGEX = r"^([a-z0-9_-]{4})*($|[a-z0-9_-]{3}$|[a-z0-9_-]{2}$)$"


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


def is_valid_str_arg(target: str) -> bool:
    return isinstance(target, str) and len(target.strip()) > 0


def is_http_url(url: str) -> bool:
    return urlparse(url).scheme in {"https", "http"}
