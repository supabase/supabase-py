from datetime import UTC, date, datetime, time, timedelta, timezone

import pytest

from postgrest.utils import (
    _sanitize_array_param,
    _serialize_filter_value,
    sanitize_param,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("param,name", '"param,name"'),
        ("param:name", '"param:name"'),
        ("param(name", '"param(name"'),
        ("param)name", '"param)name"'),
        ("table.column", "table.column"),
        ("table_column", "table_column"),
    ],
)
def test_sanitize_params(value: str, expected: str) -> None:
    assert sanitize_param(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (datetime(2024, 1, 1, 12, tzinfo=UTC), "2024-01-01T12:00:00+00:00"),
        (
            datetime(2024, 1, 1, 12, 30, 15, 500, tzinfo=timezone(timedelta(hours=5))),
            "2024-01-01T12:30:15.000500+05:00",
        ),
        (date(2024, 1, 1), "2024-01-01"),
        (time(12, 30), "12:30:00"),
        (time(12, 30, tzinfo=UTC), "12:30:00+00:00"),
    ],
)
def test_serialize_filter_value_renders_dates_and_times_as_iso_8601(
    value: object, expected: str
) -> None:
    assert _serialize_filter_value(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (datetime(2024, 7, 1, 12), "2024-07-01T12:00:00+00:00"),  # noqa: DTZ001
        (datetime.min, "0001-01-01T00:00:00+00:00"),  # noqa: DTZ901
        (datetime.max, "9999-12-31T23:59:59.999999+00:00"),  # noqa: DTZ901
    ],
)
def test_serialize_filter_value_takes_a_naive_datetime_as_utc(
    value: datetime, expected: str
) -> None:
    assert _serialize_filter_value(value) == expected


def test_array_elements_render_datetimes_as_iso_8601() -> None:
    value = datetime(2024, 1, 1, 12, tzinfo=UTC)

    assert _sanitize_array_param([value]) == "{2024-01-01T12:00:00+00:00}"
