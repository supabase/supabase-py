from __future__ import annotations

from typing import Any, Type, TypeVar, cast, get_origin
from urllib.parse import urlparse

from deprecation import deprecated
from httpx import AsyncClient  # noqa: F401
from httpx import Client as BaseClient  # noqa: F401
from pydantic import BaseModel

from .version import __version__


class SyncClient(BaseClient):
    @deprecated(
        "1.0.2", "3.0.0", __version__, "Use `Client` from the httpx package instead"
    )
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    @deprecated(
        "1.0.2",
        "3.0.0",
        __version__,
        "Use `close` method from `Client` in the httpx package instead",
    )
    def aclose(self) -> None:
        self.close()


def sanitize_param(param: Any) -> str:
    param_str = str(param)
    reserved_chars = ",:()"
    if any(char in param_str for char in reserved_chars):
        return f'"{param_str}"'
    return param_str


def sanitize_pattern_param(pattern: str) -> str:
    return sanitize_param(pattern.replace("%", "*"))


def is_http_url(url: str) -> bool:
    return urlparse(url).scheme in {"https", "http"}


TBaseModel = TypeVar("TBaseModel", bound=BaseModel)


def model_validate_json(model: Type[TBaseModel], contents) -> TBaseModel:
    """Compatibility layer between pydantic 1 and 2 for parsing an instance
    of a BaseModel from varied"""
    try:
        # pydantic > 2
        return model.model_validate_json(contents)
    except AttributeError:
        # pydantic < 2
        return model.parse_raw(contents)
