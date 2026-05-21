from datetime import date, datetime, time, timezone
from uuid import UUID

from postgrest.types import JSONAdapter


def test_json_adapter_accepts_python_serializable_scalars():
    payload = {
        "created_at": datetime(2026, 5, 21, 7, 30, tzinfo=timezone.utc),
        "birthday": date(2026, 5, 21),
        "starts_at": time(7, 30),
        "user_id": UUID("12345678-1234-5678-1234-567812345678"),
        "nested": [
            {
                "updated_at": datetime(2026, 5, 22, 7, 30, tzinfo=timezone.utc),
            }
        ],
    }

    assert JSONAdapter.validate_python(payload) == payload
