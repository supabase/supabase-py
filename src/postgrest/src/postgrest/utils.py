from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any

from deprecation import deprecated
from httpx import AsyncClient  # noqa: F401
from httpx import Client as BaseClient
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


def _quote(value: Any) -> str:
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def sanitize_param(param: Any) -> str:
    param_str = str(param)
    reserved_chars = ',:()"\\'
    if any(char in param_str for char in reserved_chars):
        return _quote(param_str)
    return param_str


def sanitize_array_element(element: Any) -> str:
    """Quote a single value for use inside a PostgreSQL array literal ``{...}``.

    PostgreSQL quotes an array element when it is empty, matches ``NULL``
    case-insensitively, or contains a brace, the comma delimiter, a double
    quote, a backslash, or whitespace; embedded double quotes and backslashes
    are backslash-escaped. Without this, a value such as ``"a,b"`` is emitted
    bare and parsed by PostgREST as two separate elements. ``None`` becomes an
    unquoted ``NULL`` element.
    """
    if element is None:
        return "NULL"
    element_str = str(element)
    needs_quoting = (
        element_str == ""
        or element_str.lower() == "null"
        or any(char in element_str for char in '{},"\\')
        or any(char.isspace() for char in element_str)
    )
    if not needs_quoting:
        return element_str
    return _quote(element_str)


def sanitize_array_param(values: Iterable[Any]) -> str:
    """Render an iterable as a PostgreSQL array literal ``{elem,elem,...}``,
    quoting each element as needed so values containing the comma delimiter (or
    other special characters) survive as single elements."""
    return f"{{{','.join(sanitize_array_element(value) for value in values)}}}"


def rpc_query_param(value: Any) -> Any:
    """Format an RPC argument sent in the query string, as in GET or HEAD calls.

    Lists and tuples become PostgreSQL array literals, since PostgREST keeps only
    one value when a non-variadic argument is repeated. Dictionaries become JSON
    for named json/jsonb arguments.
    """
    if isinstance(value, (list, tuple)):
        return sanitize_array_param(value)
    if isinstance(value, dict):
        return json.dumps(value, separators=(",", ":"))
    return value


def is_http_url(url: URL) -> bool:
    return url.scheme in {"https", "http"}
