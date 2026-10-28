from typing import AsyncIterator, Union

import pytest

from postgrest import AsyncPostgrestClient, SyncPostgrestClient


@pytest.fixture(params=["sync", "async"])
async def client(
    request,
) -> AsyncIterator[Union[SyncPostgrestClient, AsyncPostgrestClient]]:
    headers = {"Prefer": "count=exact"}
    if request.param == "sync":
        with SyncPostgrestClient("https://example.com", headers=headers) as client:
            yield client
    else:
        async with AsyncPostgrestClient(
            "https://example.com", headers=headers
        ) as client:
            yield client


@pytest.mark.parametrize("method", ["update", "delete"])
def test_max_affected_replaces_lenient_handling(client, method: str) -> None:
    client.headers["Prefer"] = "handling=lenient, count=exact"
    builder = client.table("records")
    query = (
        builder.update({"active": False}) if method == "update" else builder.delete()
    )
    query.max_affected(1)

    assert sorted(query.request.headers.get_list("Prefer", split_commas=True)) == [
        "count=exact",
        "handling=strict",
        "max-affected=1",
    ]


@pytest.mark.parametrize("prefer", ["", "count=exact,handling=strict"])
def test_max_affected_keeps_unrelated_preferences(client, prefer: str) -> None:
    client.headers["Prefer"] = prefer
    query = client.table("records").delete().max_affected(1)

    expected = (["count=exact"] if prefer else []) + [
        "handling=strict",
        "max-affected=1",
    ]
    assert (
        sorted(query.request.headers.get_list("Prefer", split_commas=True)) == expected
    )


@pytest.mark.parametrize("method", ["update", "delete"])
def test_max_affected_replaces_previous_limit(client, method: str) -> None:
    builder = client.table("records")
    query = (
        builder.update({"active": False}) if method == "update" else builder.delete()
    )
    query.max_affected(10).max_affected(1)

    assert sorted(query.request.headers.get_list("Prefer", split_commas=True)) == [
        "count=exact",
        "handling=strict",
        "max-affected=1",
    ]
