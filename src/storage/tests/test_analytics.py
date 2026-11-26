import json
from collections.abc import Callable
from io import BytesIO
from typing import Any
from unittest.mock import patch
from urllib.parse import urlparse

import pytest
import requests
from httpx import AsyncClient, Client, Request, Response
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession

from storage3 import AsyncStorageClient, StorageApiError, SyncStorageClient

from .utils import STORAGE_URL, call_with_client, use_async


@use_async
async def test_analytics_list_sends_camel_case_sort_params(use_async: bool) -> None:
    captured: dict[str, Any] = {}

    def handler(request: Request) -> Response:
        captured["url"] = request.url
        return Response(200, json=[])

    await call_with_client(
        use_async,
        handler,
        lambda client: client.analytics().list(
            limit=5,
            offset=10,
            sort_column="created_at",
            sort_order="desc",
            search="logs",
        ),
    )

    assert captured["url"].path.endswith("/iceberg/bucket")
    assert dict(captured["url"].params) == {
        "limit": "5",
        "offset": "10",
        "sortColumn": "created_at",
        "sortOrder": "desc",
        "search": "logs",
    }


def _analytics_error(request: Request) -> Response:
    return Response(
        404,
        json={
            "error": {
                "message": "Bucket not found",
                "type": "NoSuchBucket",
                "code": 404,
            }
        },
        request=request,
    )


_ANALYTICS_CALLS: list[Callable[[Any], Any]] = [
    lambda client: client.analytics().create("missing"),
    lambda client: client.analytics().list(),
    lambda client: client.analytics().delete("missing"),
]


@use_async
@pytest.mark.parametrize("action", _ANALYTICS_CALLS, ids=["create", "list", "delete"])
async def test_analytics_raises_the_server_error(
    use_async: bool, action: Callable[[Any], Any]
) -> None:
    with pytest.raises(StorageApiError) as exc_info:
        await call_with_client(use_async, _analytics_error, action)

    assert exc_info.value.message == "Bucket not found"
    assert exc_info.value.code == "NoSuchBucket"
    assert exc_info.value.status_code == 404


def test_analytics_catalog_loads_table() -> None:
    table_metadata: dict[str, Any] = {
        "format-version": 2,
        "table-uuid": "75d23c05-b7dd-45f1-aabd-c3898e28e0a0",
        "location": "s3://warehouse/table",
        "last-sequence-number": 0,
        "last-updated-ms": 1700000000000,
        "last-column-id": 1,
        "schemas": [
            {
                "type": "struct",
                "schema-id": 0,
                "fields": [{"id": 1, "name": "id", "required": False, "type": "long"}],
            }
        ],
        "current-schema-id": 0,
        "partition-specs": [{"spec-id": 0, "fields": []}],
        "default-spec-id": 0,
        "last-partition-id": 0,
        "properties": {},
        "sort-orders": [{"order-id": 0, "fields": []}],
        "default-sort-order-id": 0,
        "snapshots": [],
        "snapshot-log": [],
        "metadata-log": [],
    }
    payloads: dict[str, dict[str, Any]] = {
        "/storage/v1/iceberg/v1/config": {
            "defaults": {},
            "overrides": {"prefix": "warehouse"},
        },
        "/storage/v1/iceberg/v1/warehouse/namespaces/analytics/tables/events": {
            "metadata-location": "s3://warehouse/table/metadata/v1.metadata.json",
            "metadata": table_metadata,
        },
    }

    def get(url: str, **_: Any) -> requests.Response:
        response = requests.Response()
        response.status_code = 200
        response.raw = BytesIO(json.dumps(payloads[urlparse(url).path]).encode())
        return response

    client = SyncStorageClient(
        STORAGE_URL, {"apiKey": "service-key"}, http_session=HttpxSession(Client())
    )
    with patch("requests.sessions.Session.get", side_effect=get):
        catalog = client.analytics().catalog("warehouse", "access-key", "secret-key")
        table = catalog.load_table(("analytics", "events"))

    assert table.name() == ("analytics", "events")
    assert table.schema().find_field("id").field_id == 1


def test_analytics_catalog_refuses_update_namespace_properties() -> None:
    config: dict[str, Any] = {"defaults": {}, "overrides": {"prefix": "warehouse"}}

    def get(url: str, **_: Any) -> requests.Response:
        response = requests.Response()
        response.status_code = 200
        response.raw = BytesIO(json.dumps(config).encode())
        return response

    client = SyncStorageClient(
        STORAGE_URL, {"apiKey": "service-key"}, http_session=HttpxSession(Client())
    )
    with (
        patch("requests.sessions.Session.get", side_effect=get),
        patch("requests.sessions.Session.post") as post,
    ):
        catalog = client.analytics().catalog("warehouse", "access-key", "secret-key")
        with pytest.raises(NotImplementedError, match="namespace properties"):
            catalog.update_namespace_properties("analytics", updates={"owner": "me"})

    post.assert_not_called()


def test_analytics_catalog_without_api_key_raises_value_error() -> None:
    sync_client = SyncStorageClient(
        STORAGE_URL, {}, http_session=HttpxSession(Client())
    )
    async_client = AsyncStorageClient(
        STORAGE_URL, {}, http_session=AsyncHttpxSession(AsyncClient())
    )

    with pytest.raises(ValueError, match="apiKey"):
        sync_client.analytics().catalog("warehouse", "access-key", "secret-key")
    with pytest.raises(ValueError, match="apiKey"):
        async_client.analytics().catalog("warehouse", "access-key", "secret-key")
