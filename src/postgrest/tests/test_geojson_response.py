import pytest
from httpx import AsyncClient, Client, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession
from supabase_utils.types import JSON

from postgrest import (
    APIError,
    AsyncPostgrestClient,
    CountMethod,
    SyncPostgrestClient,
)
from postgrest.request_builder import SingleAPIResponse

COLLECTION: dict[str, JSON] = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [0, 0]},
            "properties": {"id": 1},
        }
    ],
}


def geojson_handler(request: Request) -> Response:
    assert request.headers["Accept"] == "application/geo+json"
    return Response(200, json=COLLECTION, headers={"Content-Range": "0-0/1"})


def sync_client() -> SyncPostgrestClient:
    http = Client(transport=MockTransport(geojson_handler))
    return SyncPostgrestClient(
        "https://example.com", http_session=HttpxSession(client=http)
    )


def test_table_geojson_returns_the_feature_collection_with_the_count() -> None:
    client = sync_client()
    response = (
        client.from_("places").select("*", count=CountMethod.exact).geojson().execute()
    )
    assert response == SingleAPIResponse(data=COLLECTION, count=1)


def test_rpc_geojson_returns_the_feature_collection() -> None:
    client = sync_client()
    response = client.rpc("nearby_places", {}).geojson().execute()
    assert response == SingleAPIResponse(data=COLLECTION, count=None)


async def test_async_geojson_returns_the_feature_collection() -> None:
    http = AsyncClient(transport=MockTransport(geojson_handler))
    client = AsyncPostgrestClient(
        "https://example.com", http_session=AsyncHttpxSession(client=http)
    )
    response = await client.from_("places").select("*").geojson().execute()
    assert response == SingleAPIResponse(data=COLLECTION, count=None)


def test_geojson_that_is_not_an_object_raises_api_error() -> None:
    http = Client(transport=MockTransport(lambda _: Response(200, json=[])))
    client = SyncPostgrestClient(
        "https://example.com", http_session=HttpxSession(client=http)
    )
    with pytest.raises(APIError):
        client.from_("places").select("*").geojson().execute()


def test_strip_nulls_rejects_geojson() -> None:
    client = sync_client()
    with pytest.raises(ValueError, match=r"cannot be used with geojson\(\)"):
        client.from_("places").select("*").strip_nulls().geojson()
    with pytest.raises(ValueError, match=r"cannot be used with geojson\(\)"):
        client.rpc("nearby_places", {}).strip_nulls().geojson()
