from httpx import Request, Response

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
