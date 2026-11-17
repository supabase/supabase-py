from collections.abc import Callable
from dataclasses import dataclass, field

import pytest
from httpx import AsyncClient, Client, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession

from postgrest import (
    APIError,
    APIResponse,
    AsyncPostgrestClient,
    CountMethod,
    RPCResponse,
    SyncPostgrestClient,
)
from postgrest.request_builder import SingleAPIResponse

ROLLED_BACK = {"Preference-Applied": "return=representation, tx=rollback"}


@dataclass
class Transport:
    """Answers every request with the content and headers it is given, and
    keeps what it was sent."""

    content: bytes = b'[{"id": 1}]'
    headers: dict[str, str] = field(default_factory=lambda: dict(ROLLED_BACK))
    seen: list[Request] = field(default_factory=list)

    def handler(self, request: Request) -> Response:
        self.seen.append(request)
        return Response(200, content=self.content, headers=self.headers)

    @property
    def prefer(self) -> str:
        assert len(self.seen) == 1
        return self.seen[0].headers["Prefer"]


def sync_client(transport: Transport) -> SyncPostgrestClient:
    http = Client(transport=MockTransport(transport.handler))
    return SyncPostgrestClient(
        "https://example.com", http_session=HttpxSession(client=http)
    )


def test_a_dry_run_insert_asks_for_a_rollback_and_returns_its_rows() -> None:
    transport = Transport()

    response = sync_client(transport).from_("countries").insert({}).dry_run().execute()

    assert response == APIResponse(data=[{"id": 1}])
    assert transport.prefer == "return=representation, tx=rollback"


def test_a_dry_run_keeps_its_rollback_through_select_and_max_affected() -> None:
    transport = Transport()

    (
        sync_client(transport)
        .from_("countries")
        .update({"name": "x"}, count=CountMethod.exact)
        .dry_run()
        .eq("id", 1)
        .max_affected(1)
        .select("id")
        .execute()
    )

    preferences = {preference.strip() for preference in transport.prefer.split(",")}
    assert {"tx=rollback", "handling=strict", "count=exact"} <= preferences


def test_a_second_dry_run_does_not_repeat_the_preference() -> None:
    transport = Transport()

    sync_client(transport).from_(
        "countries"
    ).delete().all().dry_run().dry_run().execute()

    assert transport.prefer == "return=representation, tx=rollback"


def run_rows(client: SyncPostgrestClient) -> object:
    return client.from_("countries").insert({}).dry_run().execute()


def run_single(client: SyncPostgrestClient) -> object:
    return client.from_("countries").insert({}).single().dry_run().execute()


def run_maybe_single(client: SyncPostgrestClient) -> object:
    return client.from_("countries").insert({}).maybe_single().dry_run().execute()


def run_csv(client: SyncPostgrestClient) -> object:
    return client.from_("countries").insert({}).csv().dry_run().execute()


def run_rpc(client: SyncPostgrestClient) -> object:
    return client.rpc("create_country", {}).dry_run().execute()


def run_rpc_count(client: SyncPostgrestClient) -> object:
    rpc = client.rpc("create_country", {}, count=CountMethod.exact, head=True)
    return rpc.dry_run().execute()


@pytest.mark.parametrize(
    "run",
    [run_rows, run_single, run_maybe_single, run_csv, run_rpc, run_rpc_count],
)
@pytest.mark.parametrize(
    "headers",
    [
        pytest.param({}, id="no preference applied"),
        pytest.param({"Preference-Applied": "return=representation"}, id="other ones"),
    ],
)
def test_a_dry_run_that_was_committed_raises(
    run: Callable[[SyncPostgrestClient], object], headers: dict[str, str]
) -> None:
    transport = Transport(content=b'{"id": 1}', headers=headers)

    with pytest.raises(APIError, match="The dry run was committed") as error:
        run(sync_client(transport))

    assert error.value.hint is not None
    assert "tx=rollback" in transport.prefer


def test_a_rolled_back_rpc_returns_its_result() -> None:
    transport = Transport(content=b"7")

    response = sync_client(transport).rpc("next_id", {}).dry_run().execute()

    assert response == RPCResponse(data=7)
    assert transport.prefer == "tx=rollback"


def test_a_query_without_a_dry_run_ignores_preference_applied() -> None:
    transport = Transport(headers={})

    response = sync_client(transport).from_("countries").insert({}).execute()

    assert response == APIResponse(data=[{"id": 1}])


async def test_an_async_dry_run_returns_the_rolled_back_row() -> None:
    transport = Transport(content=b'{"id": 1}')
    http = AsyncClient(transport=MockTransport(transport.handler))
    client = AsyncPostgrestClient(
        "https://example.com", http_session=AsyncHttpxSession(client=http)
    )

    response = await client.from_("countries").insert({}).single().dry_run().execute()

    assert response == SingleAPIResponse(data={"id": 1}, count=None)
    assert transport.prefer == "return=representation, tx=rollback"
