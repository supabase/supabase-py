import json
from io import BytesIO
from typing import Any
from unittest.mock import patch

import pytest
from httpx import Client, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import HttpxSession

from storage3 import SyncStorageClient

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


def test_analytics_catalog_loads_table() -> None:
    pytest.importorskip("pyiceberg")
    import requests

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
    payloads: list[dict[str, Any]] = [
        {"defaults": {}, "overrides": {"prefix": "warehouse"}},
        {
            "metadata-location": "s3://warehouse/table/metadata/v1.metadata.json",
            "metadata": table_metadata,
        },
    ]
    responses = []
    for data in payloads:
        response = requests.Response()
        response.status_code = 200
        response.raw = BytesIO(json.dumps(data).encode())
        responses.append(response)

    http_session = HttpxSession(
        Client(transport=MockTransport(lambda _: Response(404)))
    )
    with SyncStorageClient(
        STORAGE_URL, {"apiKey": "service-key"}, http_session=http_session
    ) as client:
        with patch("requests.sessions.Session.get", side_effect=responses):
            catalog = client.analytics().catalog(
                "warehouse", "access-key", "secret-key"
            )
            table = catalog.load_table(("analytics", "events"))

    assert table.name() == ("analytics", "events")
    assert table.schema().find_field("id").field_id == 1
