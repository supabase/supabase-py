import json
from typing import Any

import pytest
from httpx import Request, Response

from storage3.exceptions import StorageApiError
from storage3.types import LifecycleRule, NoncurrentVersionExpiration

from .utils import call_with_client, use_async


@use_async
async def test_list_buckets_sends_the_given_options_as_query(use_async: bool) -> None:
    requests: list[Request] = []

    def handler(request: Request) -> Response:
        requests.append(request)
        return Response(200, json=[])

    buckets = await call_with_client(
        use_async,
        handler,
        lambda client: client.list_buckets(
            limit=10,
            offset=20,
            search="photo",
            sort_column="created_at",
            sort_order="desc",
        ),
    )

    assert buckets == []
    (request,) = requests
    assert request.method == "GET"
    assert request.url.path == "/storage/v1/bucket"
    assert dict(request.url.params) == {
        "limit": "10",
        "offset": "20",
        "search": "photo",
        "sortColumn": "created_at",
        "sortOrder": "desc",
    }


@use_async
async def test_list_buckets_sends_no_query_by_default(use_async: bool) -> None:
    requests: list[Request] = []

    def handler(request: Request) -> Response:
        requests.append(request)
        return Response(200, json=[])

    await call_with_client(use_async, handler, lambda client: client.list_buckets())

    assert requests[0].url.query == b""


@use_async
async def test_get_bucket_lifecycle_decodes_the_rules(use_async: bool) -> None:
    requests: list[Request] = []

    def handler(request: Request) -> Response:
        requests.append(request)
        return Response(
            200,
            json={
                "rules": [
                    {
                        "id": "keep-3",
                        "status": "Disabled",
                        "filter": {},
                        "noncurrentVersionExpiration": {
                            "noncurrentDays": 7,
                            "newerNoncurrentVersions": 3,
                        },
                    }
                ]
            },
        )

    rules = await call_with_client(
        use_async, handler, lambda client: client.get_bucket_lifecycle("docs")
    )

    assert rules == [
        LifecycleRule(
            id="keep-3",
            status="Disabled",
            noncurrent_version_expiration=NoncurrentVersionExpiration(
                noncurrent_days=7, newer_noncurrent_versions=3
            ),
        )
    ]
    (request,) = requests
    assert request.method == "GET"
    assert request.url.path == "/storage/v1/bucket/docs/lifecycle"


@use_async
async def test_get_bucket_lifecycle_keeps_an_unknown_status(use_async: bool) -> None:
    def handler(request: Request) -> Response:
        return Response(
            200,
            json={
                "rules": [
                    {
                        "id": "r1",
                        "status": "Paused",
                        "filter": {},
                        "noncurrentVersionExpiration": {"noncurrentDays": 1},
                    }
                ]
            },
        )

    rules = await call_with_client(
        use_async, handler, lambda client: client.get_bucket_lifecycle("docs")
    )

    assert rules[0].status == "Paused"


@use_async
async def test_get_bucket_lifecycle_is_empty_without_a_policy(use_async: bool) -> None:
    def handler(request: Request) -> Response:
        return Response(
            404,
            json={
                "statusCode": "404",
                "code": "NoSuchLifecycleConfiguration",
                "error": "not_found",
                "message": "The lifecycle configuration does not exist",
            },
        )

    rules = await call_with_client(
        use_async, handler, lambda client: client.get_bucket_lifecycle("docs")
    )

    assert rules == []


@use_async
async def test_get_bucket_lifecycle_raises_other_errors(use_async: bool) -> None:
    def handler(request: Request) -> Response:
        return Response(
            400,
            json={
                "statusCode": "400",
                "code": "FeatureNotEnabled",
                "error": "FeatureNotEnabled",
                "message": "Lifecycle is not enabled",
            },
        )

    with pytest.raises(StorageApiError) as error:
        await call_with_client(
            use_async, handler, lambda client: client.get_bucket_lifecycle("docs")
        )

    assert error.value.code == "FeatureNotEnabled"


@use_async
async def test_update_bucket_lifecycle_puts_the_rules_with_an_empty_filter(
    use_async: bool,
) -> None:
    requests: list[Request] = []

    def handler(request: Request) -> Response:
        requests.append(request)
        return Response(
            200,
            json={
                "rules": [
                    {
                        "id": "generated",
                        "status": "Enabled",
                        "filter": {},
                        "noncurrentVersionExpiration": {"noncurrentDays": 30},
                    }
                ]
            },
        )

    rules = await call_with_client(
        use_async,
        handler,
        lambda client: client.update_bucket_lifecycle(
            "docs",
            [
                LifecycleRule(
                    noncurrent_version_expiration=NoncurrentVersionExpiration(
                        noncurrent_days=30
                    )
                )
            ],
        ),
    )

    assert [rule.id for rule in rules] == ["generated"]
    (request,) = requests
    assert request.method == "PUT"
    assert request.url.path == "/storage/v1/bucket/docs/lifecycle"
    assert json.loads(request.content) == {
        "rules": [
            {
                "status": "Enabled",
                "filter": {},
                "noncurrentVersionExpiration": {"noncurrentDays": 30},
            }
        ]
    }


@use_async
async def test_delete_bucket_lifecycle_sends_delete(use_async: bool) -> None:
    requests: list[Request] = []

    def handler(request: Request) -> Response:
        requests.append(request)
        return Response(200, json={"message": "Successfully deleted"})

    response = await call_with_client(
        use_async, handler, lambda client: client.delete_bucket_lifecycle("docs")
    )

    assert response.message == "Successfully deleted"
    (request,) = requests
    assert request.method == "DELETE"
    assert request.url.path == "/storage/v1/bucket/docs/lifecycle"


@use_async
async def test_update_bucket_lifecycle_sends_back_fields_it_does_not_know(
    use_async: bool,
) -> None:
    stored_rule = {
        "id": "r1",
        "status": "Enabled",
        "filter": {"prefix": "logs/"},
        "expiredObjectDeleteMarker": True,
        "noncurrentVersionExpiration": {"noncurrentDays": 7, "unit": "days"},
    }
    requests: list[Request] = []

    def handler(request: Request) -> Response:
        requests.append(request)
        return Response(200, json={"rules": [stored_rule]})

    def write_back(client: Any) -> Any:
        return client.update_bucket_lifecycle(
            "docs", client.get_bucket_lifecycle("docs")
        )

    async def write_back_async(client: Any) -> Any:
        rules = await client.get_bucket_lifecycle("docs")
        return await client.update_bucket_lifecycle("docs", rules)

    await call_with_client(
        use_async, handler, write_back_async if use_async else write_back
    )

    assert json.loads(requests[1].content) == {"rules": [stored_rule]}
