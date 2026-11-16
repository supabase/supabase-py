from collections.abc import Callable

from httpx import AsyncClient, Client, MockTransport, Request, Response
from pydantic import BaseModel
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession

from postgrest import AsyncPostgrestClient, SyncPostgrestClient, Table


class ItemRow(BaseModel):
    id: int


ITEMS = Table("items", ItemRow)


def profiles(request: Request) -> tuple[list[str], list[str]]:
    return (
        request.headers.get_list("Accept-Profile"),
        request.headers.get_list("Content-Profile"),
    )


def recording_handler(seen: list[Request]) -> Callable[[Request], Response]:
    def handler(request: Request) -> Response:
        seen.append(request)
        return Response(200, json=[])

    return handler


def test_sync_schema_switches_replace_the_profile_headers() -> None:
    seen: list[Request] = []
    client = SyncPostgrestClient(
        "https://example.com",
        http_session=HttpxSession(
            client=Client(transport=MockTransport(recording_handler(seen)))
        ),
    )

    other = client.schema("private").schema("other")
    client.from_("items").select("*").execute()
    other.from_("items").select("*").execute()
    other.rpc("hello", {}).execute()
    other.table(ITEMS).select().execute()
    other.from_("items").insert({"id": 1}).execute()

    assert [profiles(request) for request in seen] == [
        (["public"], ["public"]),
        (["other"], ["other"]),
        (["other"], ["other"]),
        (["other"], ["other"]),
        (["other"], ["other"]),
    ]


async def test_async_schema_switches_replace_the_profile_headers() -> None:
    seen: list[Request] = []
    async with AsyncClient(transport=MockTransport(recording_handler(seen))) as http:
        client = AsyncPostgrestClient(
            "https://example.com", http_session=AsyncHttpxSession(client=http)
        )

        other = client.schema("private").schema("other")
        await client.from_("items").select("*").execute()
        await other.from_("items").select("*").execute()
        await other.rpc("hello", {}).execute()
        await other.table(ITEMS).select().execute()
        await other.from_("items").insert({"id": 1}).execute()

    assert [profiles(request) for request in seen] == [
        (["public"], ["public"]),
        (["other"], ["other"]),
        (["other"], ["other"]),
        (["other"], ["other"]),
        (["other"], ["other"]),
    ]
