"""The RPC builders as the type checkers see them.

`test_typecheck.py` runs mypy, pyright and pyrefly on this file and asserts
that each reports an error on every line marked `# error:` and on no other
line. The pyrefly check of the package excludes this directory.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, assert_type

from supabase_utils.http.io import AsyncHttpIO, SyncHttpIO

from postgrest import TextAPIResponse
from postgrest.request_builder import RPCCountRequestBuilder, TextRequestBuilder
from postgrest.types import CountMethod

if TYPE_CHECKING:
    from postgrest import AsyncPostgrestClient, SyncPostgrestClient


def sync_rpc(client: SyncPostgrestClient) -> None:
    query = client.rpc("fn", {}).csv()
    assert_type(query, TextRequestBuilder[SyncHttpIO])
    assert_type(query.execute(), TextAPIResponse)
    counted = client.rpc("fn", {}, count=CountMethod.exact).csv()
    assert_type(counted, TextRequestBuilder[SyncHttpIO])
    assert_type(
        client.rpc("fn", {}, count=CountMethod.exact, head=True),
        RPCCountRequestBuilder[SyncHttpIO],
    )


async def async_rpc(client: AsyncPostgrestClient) -> None:
    query = client.rpc("fn", {}).csv()
    assert_type(query, TextRequestBuilder[AsyncHttpIO])
    assert_type(await query.execute(), TextAPIResponse)


def rejected(client: SyncPostgrestClient) -> None:
    client.rpc("fn", {}).csv().strip_nulls()  # error: nothing chains after csv()
    client.rpc("fn", {}).csv().eq("id", 1)  # error: nothing chains after csv()
    client.rpc("fn", {}, head=True, count=None, get=False).csv()  # error: no csv()
    client.rpc("fn", {}, count=CountMethod.exact, head=True).csv()  # error: no csv()
