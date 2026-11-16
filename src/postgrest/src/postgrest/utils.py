from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterable

    from yarl import URL


def _serialize_filter_value(value: Any) -> str:
    """Serialize a filter value into the wire format PostgREST expects.

    ``None`` maps to ``null``, booleans to ``true``/``false``, and dicts/lists
    to compact JSON, instead of the plain ``str()`` result (e.g. ``"None"``).

    A ``datetime`` becomes ISO 8601 with its UTC offset, so the server does
    not read it in the database time zone. A naive ``datetime`` is taken as
    UTC.
    """
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return json.dumps(value, separators=(",", ":"))
    if isinstance(value, datetime):
        if value.utcoffset() is None:
            value = value.replace(tzinfo=UTC)
        return value.isoformat()
    return str(value)


def _in_members(values: Iterable[Any]) -> tuple[Any, ...]:
    """`values` as a tuple, rejecting `None`, since PostgREST reads every
    member of an `in` list as a quoted literal, so `null` there is the text
    `'null'` and never matches a `NULL` row."""
    members = tuple(values)
    if any(member is None for member in members):
        raise ValueError(
            "in_() cannot match NULL, use is_() for NULL or combine it with or_()"
        )
    return members


def _quote(text: str) -> str:
    """`text` in double quotes, with the backslashes and double quotes inside
    escaped by a backslash, as every PostgREST and Postgres literal reads a
    quoted value."""
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def sanitize_param(param: Any) -> str:
    param_str = str(param)
    reserved_chars = ',:()"\\'
    if any(char in param_str for char in reserved_chars):
        return _quote(param_str)
    return param_str


_JSON_ARROW = re.compile(r"(->>?)")
_BARE_JSON_KEY = re.compile(r"-?[0-9]+|[A-Za-z_$][A-Za-z0-9_$]*")


def _sanitize_json_key(key: str) -> str:
    """A JSON path operand as PostgREST reads it: an integer stays bare as an
    array index, a key that is already double-quoted is kept, and any other
    key that is not a plain identifier is quoted."""
    if _BARE_JSON_KEY.fullmatch(key) or (
        len(key) > 1 and key.startswith('"') and key.endswith('"')
    ):
        return key
    return _quote(key)


def _sanitize_column(column: str) -> str:
    """A filter key as PostgREST reads it: the column name quoted when it
    holds a reserved character, and each key of a JSON path such as
    `data->>key` quoted on its own, so `data->>a,b` becomes `data->>"a,b"`
    rather than one column named `data->>a,b`."""
    column_name, *path = _JSON_ARROW.split(column)
    if not path:
        return sanitize_param(column)
    arrows = path[0::2]
    keys = (_sanitize_json_key(key) for key in path[1::2])
    return sanitize_param(column_name) + "".join(
        arrow + key for arrow, key in zip(arrows, keys, strict=True)
    )


def _sanitize_array_element(element: Any) -> str:
    """Quote a single value for use inside a PostgreSQL array literal ``{...}``.

    PostgreSQL quotes an array element when it is empty, matches ``NULL``
    case-insensitively, or contains a brace, the comma delimiter, a double
    quote, a backslash, or whitespace; embedded double quotes and backslashes
    are backslash-escaped. Without this, a value such as ``"a,b"`` is emitted
    bare and parsed by PostgREST as two separate elements.
    """
    if element is None:
        return "NULL"
    element_str = _serialize_filter_value(element)
    needs_quoting = (
        element_str == ""
        or element_str.lower() == "null"
        or any(char in element_str for char in '{},"\\')
        or any(char.isspace() for char in element_str)
    )
    if not needs_quoting:
        return element_str
    return _quote(element_str)


def _sanitize_array_param(values: Iterable[Any]) -> str:
    """Render an iterable as a PostgreSQL array literal ``{elem,elem,...}``,
    quoting each element as needed so values containing the comma delimiter (or
    other special characters) survive as single elements."""
    return f"{{{','.join(_sanitize_array_element(value) for value in values)}}}"


def _rpc_query_param(value: Any) -> Any:
    """Format an RPC argument sent in the query string, as in GET or HEAD calls.

    Lists and tuples become PostgreSQL array literals, since PostgREST keeps only
    one value when a non-variadic argument is repeated.
    """
    if isinstance(value, (list, tuple)):
        return _sanitize_array_param(value)
    if value is None:
        return ""
    if isinstance(value, (str, int, float)) and not isinstance(value, bool):
        return value
    return _serialize_filter_value(value)


def is_http_url(url: URL) -> bool:
    return url.scheme in {"https", "http"} and bool(url.host)
