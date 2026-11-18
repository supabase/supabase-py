"""The generated modules at run time: rows written through a generated table
go out under their column names, function arguments are sent as JSON, and
responses decode into the generated models."""

from __future__ import annotations

import datetime
import json
import uuid
from collections.abc import Callable

from httpx import Client, MockTransport, Request, Response
from postgrest import SyncPostgrestClient
from supabase_utils.http.adapters.httpx import HttpxSession

from .goldens.hostile_schema import (
    Address,
    Class,
    ClassInsert,
    ClassRow,
    ClassUpdate,
    Functions_,
    Geo,
    Status,
)
from .goldens.supabase_schema import Books, Functions, Mood

Query = Callable[[SyncPostgrestClient], object]


def send(query: Query, response: object = None) -> Request:
    sent: list[Request] = []

    def handler(request: Request) -> Response:
        sent.append(request)
        return Response(200, json=response)

    with Client(transport=MockTransport(handler)) as http:
        query(
            SyncPostgrestClient(
                "https://example.com", http_session=HttpxSession(client=http)
            )
        )
    return sent[0]


def body(request: Request) -> object:
    return json.loads(request.content)


def test_insert_sends_aliased_columns_under_their_names() -> None:
    row: ClassInsert = {
        "name": "Ada",
        "created_at": datetime.datetime(2024, 5, 1, 12, tzinfo=datetime.UTC),
        "victory_road": "won",
        "n_2fa": True,
        "statuses": [Status.HAPPY, Status.SAY_HI],
        "address": Address.model_validate({"class": "first", "geo": Geo(lat=1.5)}),
    }

    request = send(lambda client: client.table(Class.table).insert(row).execute())

    assert request.url.path == "/class"
    assert body(request) == {
        "name": "Ada",
        "createdAt": "2024-05-01T12:00:00Z",
        "victory road": "won",
        "2fa": True,
        "statuses": ["happy", 'say "hi"'],
        "address": {"class": "first", "geo": {"lat": 1.5}},
    }


def test_update_sends_aliased_columns_under_their_names() -> None:
    changes: ClassUpdate = {"datetime_": datetime.date(2024, 5, 1), "table_": None}

    request = send(
        lambda client: client.table(Class.table)
        .update(changes)
        .where(Class.victory_road.eq("won"))
        .execute()
    )

    assert body(request) == {"datetime": "2024-05-01", "table": None}
    assert request.url.params["victory road"] == "eq.won"


def test_select_decodes_columns_into_the_row_model() -> None:
    record = {
        "2fa": False,
        "Name": None,
        "createdAt": "2024-05-01T12:00:00+00:00",
        "from": 7,
        "id": "6f1b6c1e-1d2f-4e8b-9a43-6b3c2f0a7d11",
        "name": "Ada",
        "schema": "s",
        "статус": "very-happy",
        "statuses": ["2nd"],
    }

    request = send(
        lambda client: client.table(Class.table).select().execute(), [record]
    )
    rows = ClassRow.model_validate(record)

    assert request.url.params["select"] == "*"
    assert rows.from_ == 7
    assert rows.id == uuid.UUID("6f1b6c1e-1d2f-4e8b-9a43-6b3c2f0a7d11")
    assert rows.статус is Status.VERY_HAPPY
    assert rows.statuses == [Status.N_2ND]


def test_function_arguments_are_sent_as_json() -> None:
    request = send(
        lambda client: client.rpc(
            Functions_.search_with_payload_and_place_and_status_and_when(
                payload=b"ab",
                place=Address.model_validate({"class": "first"}),
                status=Status.BACK_SLASH,
                when=datetime.datetime(2024, 5, 1, tzinfo=datetime.UTC),
            )
        ).execute()
    )

    assert request.url.path == "/rpc/search"
    assert body(request) == {
        "payload": "\\x6162",
        "place": {"street": None, "class": "first", "geo": None, "moved_on": None},
        "status": "back\\slash",
        "when": "2024-05-01T00:00:00+00:00",
    }


def test_optional_arguments_left_out_are_not_sent() -> None:
    request = send(
        lambda client: client.rpc(
            Functions_.search_with_arguments_and_from_and_ids_and_limit_and_read_only_and_type(
                arguments_="a",
                type_="t",
                ids=[uuid.UUID(int=1)],
                read_only_=False,
            )
        ).execute(),
        [],
    )

    assert body(request) == {
        "arguments": "a",
        "type": "t",
        "ids": ["00000000-0000-0000-0000-000000000001"],
        "read_only": False,
    }


def test_read_only_call_is_a_get() -> None:
    request = send(
        lambda client: client.rpc(
            Functions.search_books(query="dune", mood=Mood.VERY_HAPPY, read_only=True)
        )
        .where(Books.in_print.eq(True))
        .execute(),
        [],
    )

    assert request.method == "GET"
    assert request.url.params["query"] == "dune"
    assert request.url.params["mood"] == "very happy"
    assert request.url.params["in_print"] == "eq.true"
