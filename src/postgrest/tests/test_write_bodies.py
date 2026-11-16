"""The bodies `insert()`, `upsert()` and `update()` send, for the rows the
`Insert` and `Update` TypedDicts of `supabase gen types --lang python`
describe: a `datetime` or a `UUID` as its string and `bytes` as the `\\x`
hex text PostgreSQL reads for `bytea`."""

import datetime
import json
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated, Any, NotRequired, TypedDict

import pytest
from httpx import Client, MockTransport, Request, Response
from pydantic import BaseModel, Field, JsonValue
from supabase_utils.http.adapters.httpx import HttpxSession

from postgrest import SyncPostgrestClient


class PublicEventsInsert(TypedDict):
    id: NotRequired[Annotated[uuid.UUID, Field(alias="id")]]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    day: NotRequired[Annotated[datetime.date | None, Field(alias="day")]]
    starts_at: NotRequired[Annotated[datetime.time, Field(alias="starts_at")]]
    payload: NotRequired[Annotated[bytes | None, Field(alias="payload")]]
    data: NotRequired[Annotated[JsonValue | None, Field(alias="data")]]
    tags: NotRequired[Annotated[list[str], Field(alias="tags")]]
    name: Annotated[str, Field(alias="name")]


class PublicEventsUpdate(TypedDict, total=False):
    id: Annotated[uuid.UUID, Field(alias="id")]
    created_at: Annotated[datetime.datetime, Field(alias="created_at")]
    payload: Annotated[bytes | None, Field(alias="payload")]
    name: Annotated[str, Field(alias="name")]


EVENT_ID = uuid.UUID("6f1b6c1e-1d2f-4e8b-9a43-6b3c2f0a7d11")
EVENT_ROW: PublicEventsInsert = {
    "id": EVENT_ID,
    "created_at": datetime.datetime(2024, 5, 1, 12, 30, tzinfo=datetime.UTC),
    "day": datetime.date(2024, 5, 1),
    "starts_at": datetime.time(9, 15),
    "payload": b"ab",
    "data": {"nested": [1, None, "x"]},
    "tags": ["a", "b"],
    "name": "launch",
}
ENCODED_EVENT_ROW = {
    "id": "6f1b6c1e-1d2f-4e8b-9a43-6b3c2f0a7d11",
    "created_at": "2024-05-01T12:30:00Z",
    "day": "2024-05-01",
    "starts_at": "09:15:00",
    "payload": "\\x6162",
    "data": {"nested": [1, None, "x"]},
    "tags": ["a", "b"],
    "name": "launch",
}

Query = Callable[[SyncPostgrestClient], object]


def send(query: Query) -> Request:
    sent: list[Request] = []

    def handler(request: Request) -> Response:
        sent.append(request)
        return Response(201, json=[])

    with Client(transport=MockTransport(handler)) as http:
        query(
            SyncPostgrestClient(
                "https://example.com", http_session=HttpxSession(client=http)
            )
        )
    return sent[0]


def test_insert_sends_a_generated_row_as_json() -> None:
    request = send(lambda client: client.from_("events").insert(EVENT_ROW).execute())

    assert request.method == "POST"
    assert request.headers["Content-Type"] == "application/json"
    assert json.loads(request.content) == ENCODED_EVENT_ROW


def test_bulk_insert_sends_the_rows_and_their_columns() -> None:
    rows: list[PublicEventsInsert] = [EVENT_ROW, {"name": "other"}]

    request = send(lambda client: client.from_("events").insert(rows).execute())

    assert json.loads(request.content) == [ENCODED_EVENT_ROW, {"name": "other"}]
    assert set(request.url.params["columns"].split(",")) == {
        f'"{key}"' for key in ENCODED_EVENT_ROW
    }


def test_bulk_insert_of_a_tuple_sends_the_columns_too() -> None:
    rows: tuple[PublicEventsInsert, ...] = (
        {"name": "a"},
        {"name": "b", "id": EVENT_ID},
    )

    request = send(lambda client: client.from_("events").insert(rows).execute())

    assert json.loads(request.content) == [
        {"name": "a"},
        {"name": "b", "id": str(EVENT_ID)},
    ]
    assert request.url.params["columns"] == '"name","id"'


def test_upsert_sends_a_generated_row_as_json() -> None:
    request = send(
        lambda client: client.from_("events")
        .upsert(EVENT_ROW, on_conflict="id")
        .execute()
    )

    assert request.method == "POST"
    assert request.url.params["on_conflict"] == "id"
    assert json.loads(request.content) == ENCODED_EVENT_ROW


def test_update_sends_a_generated_row_as_json() -> None:
    changes: PublicEventsUpdate = {
        "created_at": datetime.datetime(2024, 6, 1, tzinfo=datetime.UTC),
        "payload": None,
        "name": "renamed",
    }

    request = send(
        lambda client: client.from_("events")
        .update(changes)
        .eq("id", str(EVENT_ID))
        .execute()
    )

    assert request.method == "PATCH"
    assert json.loads(request.content) == {
        "created_at": "2024-06-01T00:00:00Z",
        "payload": None,
        "name": "renamed",
    }


@pytest.mark.parametrize(
    ("payload", "encoded"),
    [
        (b"\x00\xff", "\\x00ff"),
        (bytearray(b"ab"), "\\x6162"),
        (memoryview(b"ab"), "\\x6162"),
        (b"", "\\x"),
        ([b"a", b"b"], ["\\x61", "\\x62"]),
    ],
    ids=["non-utf-8", "bytearray", "memoryview", "empty", "array"],
)
def test_bytes_are_sent_as_hex_for_bytea(payload: object, encoded: object) -> None:
    request = send(
        lambda client: client.from_("events").insert({"payload": payload}).execute()
    )

    assert json.loads(request.content) == {"payload": encoded}


class Event(BaseModel):
    name: str
    payload: bytes | None = None


@dataclass
class EventRecord:
    name: str
    payload: bytes


def test_bytes_inside_a_model_or_a_dataclass_are_sent_as_hex() -> None:
    rows: list[Any] = [Event(name="a", payload=b"\x00\xff"), EventRecord("b", b"ab")]

    request = send(lambda client: client.from_("events").insert(rows).execute())

    assert json.loads(request.content) == [
        {"name": "a", "payload": "\\x00ff"},
        {"name": "b", "payload": "\\x6162"},
    ]


@pytest.mark.parametrize(
    ("method", "body"),
    [
        ("insert", {"payload": object()}),
        ("insert", "launch"),
        ("insert", [{"name": "a"}, "b"]),
        ("upsert", 7),
        ("update", {"payload": object()}),
        ("update", [{"name": "a"}]),
    ],
)
def test_a_body_that_is_not_rows_of_json_is_rejected(method: str, body: object) -> None:
    with Client() as http:
        client = SyncPostgrestClient(
            "https://example.com", http_session=HttpxSession(client=http)
        )
        write = getattr(client.from_("events"), method)

        with pytest.raises(TypeError, match=f"{method}\\(\\) takes a"):
            write(body)
