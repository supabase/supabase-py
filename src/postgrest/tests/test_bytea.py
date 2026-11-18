from __future__ import annotations

import pytest
from pydantic import BaseModel, TypeAdapter, ValidationError

from postgrest import Bytea, NullableColumn
from postgrest.utils import _rpc_query_param

ADAPTER = TypeAdapter(Bytea)


class FilesRow(BaseModel):
    payload: Bytea | None = None


@pytest.mark.parametrize(
    ("text", "decoded"),
    [
        ("\\x4869", b"Hi"),
        ("\\x", b""),
        ("\\xDEADbeef", b"\xde\xad\xbe\xef"),
        ("Hi\\\\x\\001\\377", b"Hi\\x\x01\xff"),
    ],
)
def test_decodes_the_hex_and_escape_forms(text: str, decoded: bytes) -> None:
    value = ADAPTER.validate_python(text)

    assert value == decoded
    assert isinstance(value, Bytea)


def test_takes_bytes_as_they_are() -> None:
    assert ADAPTER.validate_python(bytearray(b"\x00\xff")) == b"\x00\xff"


@pytest.mark.parametrize("text", ["\\x4", "\\xzz", "\\9", "back\\slash", "é"])
def test_rejects_text_that_is_no_bytea(text: str) -> None:
    with pytest.raises(ValidationError):
        ADAPTER.validate_python(text)


def test_a_model_decodes_and_dumps_the_hex_form() -> None:
    row = FilesRow.model_validate({"payload": "\\xff00"})

    assert row.payload == b"\xff\x00"
    assert row.model_dump() == {"payload": b"\xff\x00"}
    assert row.model_dump(mode="json") == {"payload": "\\xff00"}


def test_filters_send_bytes_in_the_hex_form() -> None:
    payload = NullableColumn[FilesRow, bytes]("payload")

    assert payload.eq(Bytea(b"Hi"))._query_parameters() == [("payload", "eq.\\x4869")]
    assert _rpc_query_param(b"Hi") == "\\x4869"
