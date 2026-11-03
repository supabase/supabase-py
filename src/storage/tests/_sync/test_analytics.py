import json
from io import BytesIO
from unittest.mock import patch

import pytest
from storage3 import SyncStorageClient

pytest.importorskip("pyiceberg")

from requests import Response


def test_catalog_load_table() -> None:
    table_response = {
        "metadata-location": "s3://warehouse/table/metadata/v1.metadata.json",
        "metadata": {
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
                    "fields": [
                        {"id": 1, "name": "id", "required": False, "type": "long"}
                    ],
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
        },
    }
    responses = []
    for data in [
        {"defaults": {}, "overrides": {"prefix": "warehouse"}},
        table_response,
    ]:
        response = Response()
        response.status_code = 200
        response.raw = BytesIO(json.dumps(data).encode())
        responses.append(response)

    with SyncStorageClient(
        "https://example.com/storage/v1/", {"apiKey": "service-key"}
    ) as storage:
        with patch("requests.sessions.Session.get", side_effect=responses):
            catalog = storage.analytics().catalog("warehouse", "s3-access", "s3-secret")
            table = catalog.load_table(("analytics", "events"))

    assert table.name() == ("analytics", "events")
    assert table.schema().find_field("id").field_id == 1
