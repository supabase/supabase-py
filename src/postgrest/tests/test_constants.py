from datetime import datetime
from typing import TypedDict

from postgrest.constants import NOW


class GeneratedUpdate(TypedDict, total=False):
    updated_at: datetime


def test_now_is_compatible_with_generated_datetime_fields() -> None:
    payload = GeneratedUpdate(updated_at=NOW)

    assert payload == {"updated_at": "now()"}
