from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Self

from pydantic_core import core_schema

if TYPE_CHECKING:
    from pydantic import GetCoreSchemaHandler

_ESCAPE = re.compile(rb"\\\\|\\([0-7]{3})")
_ESCAPE_FORM = re.compile(rb"(?:[^\\]|\\\\|\\[0-7]{3})*")


class Bytea(bytes):
    """The bytes of a PostgreSQL `bytea`, which PostgREST sends and takes as
    text in the `\\x…` hex form, `\\x4869` for `b"Hi"`.

    A pydantic field or a `TypeAdapter` of this type decodes that text, and
    the older escape form, into the bytes, and takes `bytes` as they are.
    Dumped to JSON, it is the hex form again. The generator types the
    `bytea` columns of row models as `Bytea`. Plain `bytes` are accepted
    wherever a value is written or filtered by, since the client sends every
    `bytes` in the hex form.
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: type[Any], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_plain_validator_function(
            cls._validated,
            json_schema_input_schema=core_schema.str_schema(),
            serialization=core_schema.plain_serializer_function_ser_schema(
                _hex, when_used="json", return_schema=core_schema.str_schema()
            ),
        )

    @classmethod
    def _validated(cls, value: object) -> Self:
        if isinstance(value, (bytes, bytearray, memoryview)):
            return cls(value)
        if isinstance(value, str):
            return cls(_decoded(value))
        raise ValueError(f"a bytea is bytes or its text, not {type(value).__name__}")


def _hex(value: bytes) -> str:
    return "\\x" + value.hex()


def _decoded(text: str) -> bytes:
    """The bytes of `text`, a `bytea` in the hex form, or in the escape form,
    where a byte outside printable ASCII is a backslash and its three octal
    digits, and a backslash is doubled."""
    if text.startswith("\\x"):
        return bytes.fromhex(text[2:])
    try:
        escaped = text.encode("ascii")
    except UnicodeEncodeError as error:
        raise ValueError("a bytea in the escape form is ASCII text") from error
    if not _ESCAPE_FORM.fullmatch(escaped):
        raise ValueError("a bytea in the escape form has an invalid escape")
    return _ESCAPE.sub(_unescaped, escaped)


def _unescaped(match: re.Match[bytes]) -> bytes:
    """The byte an escape of the escape form stands for."""
    octal = match[1]
    return b"\\" if octal is None else bytes([int(octal, 8)])
