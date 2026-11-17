from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from pydantic import TypeAdapter
from pydantic_core import PydanticSerializationError, to_jsonable_python
from supabase_utils.types import JSONParser

if TYPE_CHECKING:
    from supabase_utils.types import JSON
    from yarl import URL

_PYTHON: TypeAdapter[Any] = TypeAdapter(Any)


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


def _serialize_json_filter_value(value: Any) -> str:
    """Serialize a filter value as compact JSON, the operand of a filter on
    a JSON path read with `->`, so the string `Ada` is sent as `"Ada"`."""
    return json.dumps(to_jsonable_python(value), separators=(",", ":"))


def _hex_bytes(value: object) -> object:
    """`value`, dumped to plain Python, with every `bytes` in it as the `\\x`
    hex text PostgreSQL reads for `bytea`, which pydantic would otherwise
    send decoded as UTF-8."""
    if isinstance(value, (bytes, bytearray, memoryview)):
        return "\\x" + bytes(value).hex()
    if isinstance(value, Mapping):
        mapping: Mapping[object, object] = value
        return {key: _hex_bytes(item) for key, item in mapping.items()}
    if isinstance(value, Iterable) and not isinstance(value, str):
        items: Iterable[object] = value
        return [_hex_bytes(item) for item in items]
    return value


def _jsonable(value: object, error: str) -> JSON:
    """`value` as plain JSON, serialized the way pydantic serializes it, so a
    `datetime` or a `UUID` becomes its string, with `bytes` as the `\\x` hex
    text PostgreSQL reads for `bytea`, or `TypeError` with `error` when it
    cannot be.

    Pydantic first dumps the value to plain Python, so a model or a
    dataclass becomes a mapping and the `bytes` it holds are reached.
    """
    try:
        plain = _hex_bytes(_PYTHON.dump_python(value, mode="python"))
        jsonable = to_jsonable_python(plain)
    except PydanticSerializationError as cause:
        raise TypeError(error) from cause
    return JSONParser.validate_python(jsonable)


def _rows_payload(rows: object, method: str) -> JSON:
    """`rows` as the payload of the write `method`: one JSON object for a
    row, a list of them for an iterable of rows, or `TypeError`."""
    error = (
        f"{method}() takes a row, a mapping of column names to values, or an "
        "iterable of rows"
    )
    payload = _jsonable(rows, error)
    if isinstance(payload, Mapping):
        return payload
    if (
        isinstance(payload, Sequence)
        and not isinstance(payload, str)
        and all(isinstance(row, Mapping) for row in payload)
    ):
        return list(payload)
    raise TypeError(error)


def _row_payload(values: object, method: str) -> JSON:
    """`values` as the payload of the write `method`: one JSON object, or
    `TypeError`."""
    error = f"{method}() takes a mapping of column names to values"
    payload = _jsonable(values, error)
    if isinstance(payload, Mapping):
        return payload
    raise TypeError(error)


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


_CAST = re.compile(r"::[A-Za-z0-9]+$")
_QUOTED_JSON_KEY = r'"(?:[^"\\]|\\.)*"'
_JSON_PATH_STEP = re.compile(
    rf"(->>?)({_QUOTED_JSON_KEY}(?=->|$)|(?:(?!->).)*)", re.DOTALL
)
_BARE_JSON_KEY = re.compile(
    rf"-?[0-9]+|[A-Za-z_$][A-Za-z0-9_$]*|{_QUOTED_JSON_KEY}", re.DOTALL
)


def _sanitize_json_key(key: str) -> str:
    """A JSON path operand as PostgREST reads it: an integer stays bare as an
    array index, a key that is already double-quoted is kept, and any other
    key that is not a plain identifier is quoted."""
    if not key:
        raise ValueError("a JSON path cannot end with an empty key")
    if _BARE_JSON_KEY.fullmatch(key):
        return key
    return _quote(key)


def _sanitize_column(column: str) -> str:
    """A filter key as PostgREST reads it: the column name quoted when it
    holds a reserved character, and each key of a JSON path such as
    `data->>key` quoted on its own, so `data->>a,b` becomes `data->>"a,b"`
    rather than one column named `data->>a,b`. A trailing cast such as
    `::int` stays outside the quotes."""
    cast_match = _CAST.search(column)
    cast = cast_match.group() if cast_match else ""
    column = column.removesuffix(cast)
    path_start = column.find("->")
    if path_start == -1:
        return sanitize_param(column) + cast
    sanitized = [sanitize_param(column[:path_start])]
    position = path_start
    while position < len(column):
        step = _JSON_PATH_STEP.match(column, position)
        assert step is not None
        arrow, key = step.groups()
        sanitized.append(arrow + _sanitize_json_key(key))
        position = step.end()
    return "".join(sanitized) + cast


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
