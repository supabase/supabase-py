from typing import Any

from httpx import Request, Response

from .utils import call_with_client, use_async


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
