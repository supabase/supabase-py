from datetime import date
from typing import Annotated, Any

import pytest
from pydantic import BaseModel, Field, JsonValue

from postgrest import (
    Column,
    ColumnExpression,
    ComputedField,
    DerivedExpression,
    Expression,
    Filter,
    JsonPath,
    NullableColumn,
    Ordering,
    PartialRow,
    Table,
    TableOperation,
    TableRequest,
)
from postgrest.request_builder import _cleaned_columns
from postgrest.table_executor import _render


class ItemRow(BaseModel):
    id: int
    rating: Annotated[int, Field(ge=0, le=5)]
    price: float
    sold_on: date | None = None
    data: dict[str, JsonValue] | None = None


class Items:
    id = Column[ItemRow, int]("id")
    rating = Column[ItemRow, int]("rating")
    price = Column[ItemRow, float]("price")
    sold_on = NullableColumn[ItemRow, date]("sold_on")
    data = NullableColumn[ItemRow, JsonValue]("data")
    table = Table("items", ItemRow, primary_key=(id,))


def select_list(*columns: Expression[ItemRow, Any]) -> str | None:
    request = TableRequest(
        table=Items.table, operation=TableOperation.SELECT, columns=columns
    )
    return _render(request).query.get("select")


def parameters(filter: Filter[ItemRow]) -> list[tuple[str, str]]:
    return filter._query_parameters()


def row(
    *columns: Expression[ItemRow, Any], json: dict[str, Any]
) -> PartialRow[ItemRow]:
    return PartialRow(Items.table, columns, json)


class TestJsonPaths:
    def test_a_path_quotes_its_keys_and_leaves_indexes_bare(self) -> None:
        assert Items.data.json_text("name").expression == 'data->>"name"'
        assert Items.data.json_object("0").expression == 'data->"0"'
        assert Items.data.json_object("tags").json_text_at(-1).expression == (
            'data->"tags"->>-1'
        )
        assert Items.data.json_object_at(2).expression == "data->2"

    def test_a_key_with_quotes_is_escaped(self) -> None:
        assert Items.data.json_text('a "b"\\c').expression == r'data->>"a \"b\"\\c"'

    def test_a_path_is_a_column_expression(self) -> None:
        path = Items.data.json_text("name")

        assert isinstance(path, JsonPath)
        assert isinstance(path, ColumnExpression)
        assert path == JsonPath(Items.data, "->>", "name")

    def test_a_text_path_sends_its_operand_as_text(self) -> None:
        assert parameters(Items.data.json_text("name").eq("Ada")) == [
            ('data->>"name"', "eq.Ada")
        ]

    def test_an_object_path_sends_its_operand_as_json(self) -> None:
        name = Items.data.json_object("name")

        assert parameters(name.eq("Ada")) == [('data->"name"', 'eq."Ada"')]
        assert parameters(Items.data.json_object("n").gt(2)) == [('data->"n"', "gt.2")]
        assert parameters(name.in_(["Ada", 1])) == [
            ('data->"name"', 'in.("\\"Ada\\"",1)')
        ]
        assert parameters(name.contains({"a": [1]})) == [
            ('data->"name"', 'cs.{"a":[1]}')
        ]

    def test_null_is_tested_with_is_null(self) -> None:
        name = Items.data.json_object("name")

        assert parameters(name.is_null()) == [('data->"name"', "is.null")]
        assert parameters(~Items.data.json_text("name").is_null()) == [
            ('data->>"name"', "not.is.null")
        ]

    def test_an_object_path_operand_is_escaped_inside_a_group(self) -> None:
        filter = Items.data.json_object("name").eq("a,b") | Items.id.eq(1)

        assert parameters(filter) == [("or", '(data->"name".eq."\\"a,b\\"",id.eq.1)')]

    def test_a_path_orders(self) -> None:
        assert Items.data.json_text("name").desc().order_key == 'data->>"name".desc'

    def test_a_path_is_selected_under_its_own_expression(self) -> None:
        path = Items.data.json_text("name")

        assert path.response_key == 'data->>"name"'
        assert select_list(Items.id, path) == ('id,"data->>\\"name\\"":data->>"name"')

    def test_whitespace_in_a_key_survives_the_select_list(self) -> None:
        path = Items.data.json_text("a b")

        assert select_list(path) == '"data->>\\"a b\\"":data->>"a b"'


class TestCasts:
    def test_a_cast_is_select_only(self) -> None:
        cast = Items.price.cast("text", str)

        assert isinstance(cast, DerivedExpression)
        assert not isinstance(cast, ColumnExpression)
        assert not isinstance(cast, Ordering)
        assert not hasattr(cast, "eq")

    def test_a_cast_is_selected_under_its_own_expression(self) -> None:
        cast = Items.price.cast("int", int)

        assert cast.expression == "price::int"
        assert cast.response_key == "price::int"
        assert select_list(cast) == '"price::int":price::int'

    def test_a_cast_of_a_json_path(self) -> None:
        cast = Items.data.json_text("n").cast("int", int)

        assert cast.expression == 'data->>"n"::int'
        assert select_list(cast) == '"data->>\\"n\\"::int":data->>"n"::int'

    @pytest.mark.parametrize("sql_type", ["double precision", "int)", ""])
    def test_a_type_postgrest_cannot_read_raises(self, sql_type: str) -> None:
        with pytest.raises(ValueError, match="float8"):
            Items.price.cast(sql_type, float)


class TestAggregates:
    def test_aggregates_render_as_postgrest_calls(self) -> None:
        assert select_list(
            Items.sold_on,
            Items.price.sum(),
            Items.price.avg(),
            Items.rating.min(),
            Items.rating.max(),
            Items.id.count(),
            DerivedExpression.count_all(),
        ) == (
            'sold_on,"price.sum()":price.sum(),"price.avg()":price.avg(),'
            '"rating.min()":rating.min(),"rating.max()":rating.max(),'
            '"id.count()":id.count(),"count()":count()'
        )

    def test_two_sums_get_different_keys(self) -> None:
        assert Items.price.sum().response_key != Items.rating.sum().response_key

    def test_a_cast_before_and_after_an_aggregate(self) -> None:
        assert Items.price.cast("int", int).sum().expression == "price::int.sum()"
        assert Items.price.sum().cast("text", str).expression == "price.sum()::text"

    def test_count_all_belongs_to_no_column(self) -> None:
        count = DerivedExpression.count_all()

        assert count.source is None
        assert count.expression == "count()"


class TestResponseKeys:
    def test_a_stored_column_comes_back_under_its_name(self) -> None:
        assert Items.price.response_key == "price"
        assert select_list(Items.price) == "price"

    def test_a_long_expression_is_shortened_to_a_prefix_and_a_digest(self) -> None:
        path = Items.data.json_text("k" * 80)

        key = path.response_key
        assert len(key.encode()) == 63
        assert key == 'data->>"' + "k" * 38 + "~68fd83e9e38440e0"
        assert select_list(path) == (
            '"data->>\\"' + "k" * 38 + '~68fd83e9e38440e0":' + path.expression
        )

    def test_long_expressions_sharing_a_prefix_get_different_keys(self) -> None:
        first = Items.data.json_text("k" * 80 + "a").response_key
        second = Items.data.json_text("k" * 80 + "b").response_key

        assert first != second

    def test_a_multibyte_character_is_not_split(self) -> None:
        key = Items.data.json_text("é" * 40).response_key

        assert len(key.encode()) <= 63
        assert key.startswith('data->>"éééé')


class TestReads:
    def test_a_json_path_reads_the_decoded_json(self) -> None:
        name = Items.data.json_text("name")
        tags = Items.data.json_object("tags")
        partial = row(
            name, tags, json={name.response_key: "Ada", tags.response_key: ["a"]}
        )

        assert partial[name] == "Ada"
        assert partial[tags] == ["a"]

    def test_a_json_path_reads_none_when_absent(self) -> None:
        name = Items.data.json_text("name")

        assert row(name, json={name.response_key: None})[name] is None

    def test_a_cast_decodes_through_its_value_type(self) -> None:
        cast = Items.sold_on.cast("text", date)

        assert row(cast, json={"sold_on::text": "2024-01-02"})[cast] == date(2024, 1, 2)

    def test_min_and_max_decode_as_the_column(self) -> None:
        partial = row(
            Items.sold_on.min(),
            Items.sold_on.max(),
            json={"sold_on.min()": "2024-01-02", "sold_on.max()": "2024-03-04"},
        )

        assert partial[Items.sold_on.min()] == date(2024, 1, 2)
        assert partial[Items.sold_on.max()] == date(2024, 3, 4)

    def test_a_sum_decodes_as_the_column_without_its_constraints(self) -> None:
        partial = row(
            Items.rating.sum(),
            Items.price.sum(),
            json={"rating.sum()": 17, "price.sum()": 3},
        )

        assert partial[Items.rating.sum()] == 17
        assert partial[Items.price.sum()] == 3.0
        assert isinstance(partial[Items.price.sum()], float)

    def test_avg_and_count_decode_as_their_type(self) -> None:
        partial = row(
            Items.price.avg(),
            DerivedExpression.count_all(),
            json={"price.avg()": 2, "count()": 3},
        )

        assert partial[Items.price.avg()] == 2.0
        assert isinstance(partial[Items.price.avg()], float)
        assert partial[DerivedExpression.count_all()] == 3

    def test_an_aggregate_of_no_rows_reads_none(self) -> None:
        assert (
            row(Items.price.sum(), json={"price.sum()": None})[Items.price.sum()]
            is None
        )

    def test_an_aggregate_of_a_computed_field_decodes_through_its_value_type(
        self,
    ) -> None:
        next_sale = ComputedField[ItemRow, date]("next_sale", date)
        partial = row(next_sale.max(), json={"next_sale.max()": "2024-01-02"})

        assert partial[next_sale.max()] == date(2024, 1, 2)

    def test_reading_an_unselected_derivation_raises(self) -> None:
        partial = row(Items.price.sum(), json={"price.sum()": 1})

        with pytest.raises(KeyError, match=r"price\.avg\(\) was not selected"):
            partial[Items.price.avg()]


def test_select_cleaning_keeps_whitespace_after_an_escaped_quote() -> None:
    assert _cleaned_columns(('"a \\" b c":x', " y ")) == '"a \\" b c":x,y'
