from __future__ import annotations

import pytest

from supabase_typegen._names import (
    claim,
    constant_name,
    member_name,
    pascal_case,
    snake_case,
    unique_names,
)


@pytest.mark.parametrize(
    ("name", "pascal", "snake", "constant"),
    [
        ("author_stats", "AuthorStats", "author_stats", "AUTHOR_STATS"),
        ("createdAt", "CreatedAt", "created_at", "CREATED_AT"),
        ("victory road", "VictoryRoad", "victory_road", "VICTORY_ROAD"),
        ("very-happy", "VeryHappy", "very_happy", "VERY_HAPPY"),
        ("2fa", "N2fa", "n_2fa", "N_2FA"),
        ("статус", "Статус", "статус", "СТАТУС"),  # noqa: RUF001
        ("ﬁle", "File", "file", "FILE"),
        ("-", "Unnamed", "unnamed", "UNNAMED"),
    ],
)
def test_cases(name: str, pascal: str, snake: str, constant: str) -> None:
    assert pascal_case(name) == pascal
    assert snake_case(name) == snake
    assert constant_name(name) == constant


def test_keywords_get_a_trailing_underscore() -> None:
    assert member_name("class") == "class_"
    assert member_name("match") == "match"


def test_claim_appends_underscores_until_free() -> None:
    used = {"table", "table_"}

    assert claim(used, "table") == "table__"
    assert "table__" in used


def test_names_that_collide_keep_the_lowercase_one() -> None:
    assert unique_names(["Name", "name", "NAME"], reserved={"id"}) == {
        "Name": "name_Name",
        "name": "name",
        "NAME": "name_NAME",
    }


def test_reserved_names_are_not_claimed() -> None:
    assert unique_names(["table", "str"], reserved={"table", "str"}) == {
        "table": "table_",
        "str": "str_",
    }
