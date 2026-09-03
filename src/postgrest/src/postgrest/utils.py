from __future__ import annotations

from typing import Any, Iterable, Type, TypeVar, cast, get_origin
from urllib.parse import urlparse

from deprecation import deprecated
from httpx import AsyncClient  # noqa: F401
from httpx import Client as BaseClient  # noqa: F401
from pydantic import BaseModel
from yarl import URL

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


def sanitize_array_element(element: Any) -> str:
    """Quote a single value for use inside a PostgreSQL array literal ``{...}``.

    PostgreSQL quotes an array element when it is empty, matches ``NULL``
    case-insensitively, or contains a brace, the comma delimiter, a double
    quote, a backslash, or whitespace; embedded double quotes and backslashes
    are backslash-escaped. Without this, a value such as ``"a,b"`` is emitted
    bare and parsed by PostgREST as two separate elements.
    """
    element_str = str(element)
    needs_quoting = (
        element_str == ""
        or element_str.lower() == "null"
        or any(char in element_str for char in '{},"\\')
        or any(char.isspace() for char in element_str)
    )
    if not needs_quoting:
        return element_str
    escaped = element_str.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def sanitize_array_param(values: Iterable[Any]) -> str:
    """Render an iterable as a PostgreSQL array literal ``{elem,elem,...}``,
    quoting each element as needed so values containing the comma delimiter (or
    other special characters) survive as single elements."""
    return f"{{{','.join(sanitize_array_element(value) for value in values)}}}"


def sanitize_pattern_param(pattern: str) -> str:
    return sanitize_param(pattern.replace("%", "*"))


def is_http_url(url: URL) -> bool:
    return url.scheme in {"https", "http"}


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
