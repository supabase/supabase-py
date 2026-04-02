from typing import Any, Dict, Iterable, List

import pytest
from httpx import Client
from supabase_utils.http.adapters.httpx import HttpxSession
from supabase_utils.http.headers import Headers
from supabase_utils.http.io import SyncHttpIO
from supabase_utils.http.request import Request, Response
from supabase_utils.types import JSON, JSONParser
from yarl import URL

from postgrest.request_builder import (
    APIResponse,
    RequestBuilder,
    SingleAPIResponse,
    TextRequestBuilder,
)
from postgrest.types import CountMethod


@pytest.fixture
def request_builder() -> Iterable[RequestBuilder[SyncHttpIO]]:
    with Client() as client:
        yield RequestBuilder(
            executor=SyncHttpIO(session=HttpxSession(client=client)),
            base_url=URL("/example_table"),
            default_headers=Headers.empty(),
        )


class TestSelect:
    def test_select(self, request_builder: RequestBuilder[SyncHttpIO]) -> None:
        builder = request_builder.select("col1", "col2")

        assert builder.request.query["select"] == "col1,col2"
        assert builder.request.headers.get("prefer") is None
        assert builder.request.method == "GET"
        assert builder.request.body == {}

    def test_select_with_count(
        self, request_builder: RequestBuilder[SyncHttpIO]
    ) -> None:
        builder = request_builder.select(count=CountMethod.exact)

        assert builder.request.query["select"] == "*"
        assert builder.request.headers["prefer"] == "count=exact"
        assert builder.request.method == "GET"
        assert builder.request.body == {}

    def test_select_with_head(
        self, request_builder: RequestBuilder[SyncHttpIO]
    ) -> None:
        builder = request_builder.select("col1", "col2", head=True)

        assert builder.request.query.get("select") == "col1,col2"
        assert builder.request.headers.get("prefer") is None
        assert builder.request.method == "HEAD"
        assert builder.request.body == {}

    def test_select_as_csv(self, request_builder: RequestBuilder[SyncHttpIO]) -> None:
        builder = request_builder.select("*").csv()

        assert builder.request.headers["Accept"] == "text/csv"
        assert isinstance(builder, TextRequestBuilder)


class TestInsert:
    def test_insert(self, request_builder: RequestBuilder[SyncHttpIO]) -> None:
        builder = request_builder.insert({"key1": "val1"})

        assert builder.request.headers.get_list("prefer") == ["return=representation"]
        assert builder.request.method == "POST"
        assert builder.request.body == {"key1": "val1"}

    def test_insert_with_count(
        self, request_builder: RequestBuilder[SyncHttpIO]
    ) -> None:
        builder = request_builder.insert({"key1": "val1"}, count=CountMethod.exact)

        assert builder.request.headers.get_list("prefer") == [
            "return=representation",
            "count=exact",
        ]
        assert builder.request.method == "POST"
        assert builder.request.body == {"key1": "val1"}

    def test_insert_with_upsert(
        self, request_builder: RequestBuilder[SyncHttpIO]
    ) -> None:
        builder = request_builder.insert({"key1": "val1"}, upsert=True)

        assert builder.request.headers.get_list("prefer") == [
            "return=representation",
            "resolution=merge-duplicates",
        ]
        assert builder.request.method == "POST"
        assert builder.request.body == {"key1": "val1"}

    def test_upsert_with_default_single(
        self, request_builder: RequestBuilder[SyncHttpIO]
    ) -> None:
        builder = request_builder.upsert([{"key1": "val1"}], default_to_null=False)
        assert builder.request.headers.get_list("prefer") == [
            "return=representation",
            "resolution=merge-duplicates",
            "missing=default",
        ]
        assert builder.request.method == "POST"
        assert builder.request.body == [{"key1": "val1"}]
        assert builder.request.query.get("columns") == '"key1"'

    def test_bulk_insert_using_default(
        self, request_builder: RequestBuilder[SyncHttpIO]
    ) -> None:
        builder = request_builder.insert(
            [{"key1": "val1", "key2": "val2"}, {"key3": "val3"}], default_to_null=False
        )
        assert builder.request.headers.get_list("prefer") == [
            "return=representation",
            "missing=default",
        ]
        assert builder.request.method == "POST"
        assert builder.request.body == [
            {"key1": "val1", "key2": "val2"},
            {"key3": "val3"},
        ]
        assert set(builder.request.query["columns"].split(",")) == set(
            '"key1","key2","key3"'.split(",")
        )

    def test_upsert(self, request_builder: RequestBuilder[SyncHttpIO]) -> None:
        builder = request_builder.upsert({"key1": "val1"})

        assert builder.request.headers.get_list("prefer") == [
            "return=representation",
            "resolution=merge-duplicates",
        ]
        assert builder.request.method == "POST"
        assert builder.request.body == {"key1": "val1"}

    def test_bulk_upsert_with_default(
        self, request_builder: RequestBuilder[SyncHttpIO]
    ) -> None:
        builder = request_builder.upsert(
            [{"key1": "val1", "key2": "val2"}, {"key3": "val3"}], default_to_null=False
        )
        assert builder.request.headers.get_list("prefer") == [
            "return=representation",
            "resolution=merge-duplicates",
            "missing=default",
        ]
        assert builder.request.method == "POST"
        assert builder.request.body == [
            {"key1": "val1", "key2": "val2"},
            {"key3": "val3"},
        ]
        assert set(builder.request.query["columns"].split(",")) == set(
            '"key1","key2","key3"'.split(",")
        )


class TestUpdate:
    def test_update(self, request_builder: RequestBuilder[SyncHttpIO]) -> None:
        builder = request_builder.update({"key1": "val1"})

        assert builder.request.headers.get_list("prefer") == ["return=representation"]
        assert builder.request.method == "PATCH"
        assert builder.request.body == {"key1": "val1"}

    def test_update_with_count(
        self, request_builder: RequestBuilder[SyncHttpIO]
    ) -> None:
        builder = request_builder.update({"key1": "val1"}, count=CountMethod.exact)

        assert builder.request.headers.get_list("prefer") == [
            "return=representation",
            "count=exact",
        ]
        assert builder.request.method == "PATCH"
        assert builder.request.body == {"key1": "val1"}

    def test_update_with_max_affected(
        self, request_builder: RequestBuilder[SyncHttpIO]
    ) -> None:
        builder = request_builder.update({"key1": "val1"}).max_affected(5)

        assert "handling=strict" in builder.request.headers["prefer"]
        assert "max-affected=5" in builder.request.headers["prefer"]
        assert "return=representation" in builder.request.headers["prefer"]
        assert builder.request.method == "PATCH"
        assert builder.request.body == {"key1": "val1"}


class TestDelete:
    def test_delete(self, request_builder: RequestBuilder[SyncHttpIO]) -> None:
        builder = request_builder.delete()

        assert builder.request.headers.get_list("prefer") == ["return=representation"]
        assert builder.request.method == "DELETE"
        assert builder.request.body == {}

    def test_delete_with_count(
        self, request_builder: RequestBuilder[SyncHttpIO]
    ) -> None:
        builder = request_builder.delete(count=CountMethod.exact)

        assert builder.request.headers.get_list("prefer") == [
            "return=representation",
            "count=exact",
        ]
        assert builder.request.method == "DELETE"
        assert builder.request.body == {}

    def test_delete_with_max_affected(
        self, request_builder: RequestBuilder[SyncHttpIO]
    ) -> None:
        builder = request_builder.delete().max_affected(10)

        assert "handling=strict" in builder.request.headers["prefer"]
        assert "max-affected=10" in builder.request.headers["prefer"]
        assert "return=representation" in builder.request.headers["prefer"]
        assert builder.request.method == "DELETE"
        assert builder.request.body == {}


class TestTextSearch:
    def test_text_search(self, request_builder: RequestBuilder[SyncHttpIO]) -> None:
        builder = request_builder.select("catchphrase").text_search(
            "catchphrase",
            "'fat' & 'cat'",
            {
                "type": "plain",
                "config": "english",
            },
        )
        assert builder.request.query.get("select") == "catchphrase"
        assert (
            builder.request.query.get("catchphrase") == "plfts(english).'fat' & 'cat'"
        )


class TestExplain:
    def test_explain_plain(self, request_builder: RequestBuilder[SyncHttpIO]) -> None:
        builder = request_builder.select("*").explain()
        assert builder.request.query["select"] == "*"
        assert "application/vnd.pgrst.plan" in str(
            builder.request.headers.get("accept")
        )

    def test_explain_options(self, request_builder: RequestBuilder[SyncHttpIO]) -> None:
        builder = request_builder.select("*").explain(
            analyze=True,
            verbose=True,
            buffers=True,
            settings=False,
            wal=True,
            format="json",
        )
        assert builder.request.query["select"] == "*"
        assert "application/vnd.pgrst.plan+json;" in str(
            builder.request.headers.get("accept")
        )
        assert "options=analyze|verbose|buffers|wal" in str(
            builder.request.headers.get("accept")
        )


class TestOrder:
    def test_order(self, request_builder: RequestBuilder[SyncHttpIO]) -> None:
        builder = request_builder.select().order("country_name", desc=True)
        assert builder.request.query.get("select") == "*"
        assert builder.request.query.get("order") == "country_name.desc"

    def test_multiple_orders(self, request_builder: RequestBuilder[SyncHttpIO]) -> None:
        builder = (
            request_builder.select()
            .order("country_name", desc=True)
            .order("iso", desc=True)
        )
        assert builder.request.query.get("select") == "*"
        assert builder.request.query.get_list("order") == [
            "country_name.desc",
            "iso.desc",
        ]

    def test_multiple_orders_on_foreign_table(
        self, request_builder: RequestBuilder[SyncHttpIO]
    ) -> None:
        foreign_table = "cities"
        builder = (
            request_builder.select()
            .order("city_name", desc=True, foreign_table=foreign_table)
            .order("id", desc=True, foreign_table=foreign_table)
        )
        assert builder.request.query.get("select") == "*"
        assert builder.request.query.get_list("cities.order") == [
            "city_name.desc",
            "id.desc",
        ]


class TestRange:
    def test_range_on_own_table(
        self, request_builder: RequestBuilder[SyncHttpIO]
    ) -> None:
        builder = request_builder.select("*").range(0, 1)
        assert builder.request.query["select"] == "*"
        assert builder.request.query["limit"] == "2"
        assert builder.request.query["offset"] == "0"

    def test_range_on_foreign_table(
        self, request_builder: RequestBuilder[SyncHttpIO]
    ) -> None:
        foreign_table = "cities"
        builder = request_builder.select("*").range(1, 2, foreign_table)
        assert builder.request.query["select"] == "*"
        assert builder.request.query[f"{foreign_table}.limit"] == "2"
        assert builder.request.query[f"{foreign_table}.offset"] == "1"


@pytest.fixture
def csv_api_response() -> str:
    return "id,name\n1,foo\n"


@pytest.fixture
def api_response_with_error() -> Dict[str, Any]:
    return {
        "message": "Route GET:/countries?select=%2A not found",
        "error": "Not Found",
        "statusCode": 404,
    }


@pytest.fixture
def api_response() -> List[Dict[str, JSON]]:
    return [
        {
            "id": 1,
            "name": "Bonaire, Sint Eustatius and Saba",
            "iso2": "BQ",
            "iso3": "BES",
            "local_name": None,
            "continent": None,
        },
        {
            "id": 2,
            "name": "Curaçao",
            "iso2": "CW",
            "iso3": "CUW",
            "local_name": None,
            "continent": None,
        },
    ]


@pytest.fixture
def single_api_response() -> Dict[str, JSON]:
    return {
        "id": 1,
        "name": "Bonaire, Sint Eustatius and Saba",
        "iso2": "BQ",
        "iso3": "BES",
        "local_name": None,
        "continent": None,
    }


@pytest.fixture
def content_range_header_with_count() -> str:
    return "0-1/2"


@pytest.fixture
def content_range_header_without_count() -> str:
    return "0-1"


@pytest.fixture
def prefer_header_with_count() -> str:
    return "count=exact"


@pytest.fixture
def prefer_header_without_count() -> str:
    return "random prefer header"


@pytest.fixture
def request_response_without_prefer_header() -> Response:
    return Response(
        status=200,
        request=Request(
            method="GET",
            url=URL("http://example.com"),
            content=None,
            headers=Headers.empty(),
        ),
        content=b"",
        headers=Headers.empty(),
    )


@pytest.fixture
def request_response_with_prefer_header_without_count(
    prefer_header_without_count: str,
) -> Response:
    return Response(
        status=200,
        headers=Headers.empty(),
        content=b"",
        request=Request(
            method="GET",
            url=URL("http://example.com"),
            headers=Headers.from_mapping({"prefer": prefer_header_without_count}),
            content=None,
        ),
    )


@pytest.fixture
def request_response_with_prefer_header_with_count_and_content_range(
    prefer_header_with_count: str, content_range_header_with_count: str
) -> Response:
    return Response(
        status=200,
        headers=Headers.from_mapping(
            {"content-range": content_range_header_with_count}
        ),
        content=b"",
        request=Request(
            method="GET",
            url=URL("http://example.com"),
            headers=Headers.from_mapping({"prefer": prefer_header_with_count}),
            content=None,
        ),
    )


@pytest.fixture
def request_response_with_data(
    prefer_header_with_count: str,
    content_range_header_with_count: str,
    api_response: List[Dict[str, JSON]],
) -> Response:
    return Response(
        status=200,
        headers=Headers.from_mapping(
            {"content-range": content_range_header_with_count}
        ),
        content=JSONParser.dump_json(api_response),
        request=Request(
            method="GET",
            url=URL("http://example.com"),
            headers=Headers.from_mapping({"prefer": prefer_header_with_count}),
            content=None,
        ),
    )


@pytest.fixture
def request_response_with_single_data(
    prefer_header_with_count: str,
    content_range_header_with_count: str,
    single_api_response: Dict[str, JSON],
) -> Response:
    return Response(
        status=200,
        headers=Headers.from_mapping(
            {"content-range": content_range_header_with_count}
        ),
        content=JSONParser.dump_json(single_api_response),
        request=Request(
            method="GET",
            url=URL("http://example.com"),
            headers=Headers.from_mapping({"prefer": prefer_header_with_count}),
            content=None,
        ),
    )


@pytest.fixture
def request_response_with_csv_data(csv_api_response: str) -> Response:
    return Response(
        status=200,
        content=csv_api_response.encode("utf-8"),
        headers=Headers.empty(),
        request=Request(
            method="GET",
            url=URL("http://example.com"),
            headers=Headers.empty(),
            content=None,
        ),
    )


class TestApiResponse:
    def test_parses_valid_response_only_data(
        self, api_response: List[Dict[str, JSON]]
    ) -> None:
        result = APIResponse(data=api_response)
        assert result.data == api_response

    def test_parses_valid_response_data_and_count(
        self, api_response: List[Dict[str, JSON]]
    ) -> None:
        count = len(api_response)
        result = APIResponse(data=api_response, count=count)
        assert result.data == api_response
        assert result.count == count

    def test_get_count_from_content_range_header_with_count(
        self, content_range_header_with_count: str
    ) -> None:
        assert (
            APIResponse._get_count_from_content_range_header(
                content_range_header_with_count
            )
            == 2
        )

    def test_get_count_from_content_range_header_without_count(
        self, content_range_header_without_count: str
    ) -> None:
        assert (
            APIResponse._get_count_from_content_range_header(
                content_range_header_without_count
            )
            is None
        )

    def test_is_count_in_prefer_header_true(
        self, prefer_header_with_count: str
    ) -> None:
        assert APIResponse._is_count_in_prefer_header(prefer_header_with_count)

    def test_is_count_in_prefer_header_false(
        self, prefer_header_without_count: str
    ) -> None:
        assert not APIResponse._is_count_in_prefer_header(prefer_header_without_count)

    def test_get_count_from_http_request_response_without_prefer_header(
        self, request_response_without_prefer_header: Response
    ) -> None:
        assert (
            APIResponse._get_count_from_http_request_response(
                request_response_without_prefer_header
            )
            is None
        )

    def test_get_count_from_http_request_response_with_prefer_header_without_count(
        self, request_response_with_prefer_header_without_count: Response
    ) -> None:
        assert (
            APIResponse._get_count_from_http_request_response(
                request_response_with_prefer_header_without_count
            )
            is None
        )

    def test_get_count_from_http_request_response_with_count_and_content_range(
        self, request_response_with_prefer_header_with_count_and_content_range: Response
    ) -> None:
        assert (
            APIResponse._get_count_from_http_request_response(
                request_response_with_prefer_header_with_count_and_content_range
            )
            == 2
        )

    def test_from_http_request_response_constructor(
        self, request_response_with_data: Response, api_response: List[Dict[str, Any]]
    ) -> None:
        result = APIResponse.from_http_request_response(request_response_with_data)
        assert result.data == api_response
        assert result.count == 2

    def test_single_from_http_request_response_constructor(
        self,
        request_response_with_single_data: Response,
        single_api_response: Dict[str, Any],
    ) -> None:
        result = SingleAPIResponse.from_http_request_response(
            request_response_with_single_data
        )
        assert isinstance(result.data, dict)
        assert result.data == single_api_response
        assert result.count == 2
