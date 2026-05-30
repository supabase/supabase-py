from postgrest.types import JSON, JSONAdapter

from datetime import datetime
from uuid import UUID

def test_json_adapter():
    assert JSONAdapter.validate_python(None) is None
    assert JSONAdapter.validate_python(UUID("12345678-1234-5678-1234-567812345678")) is not None
    assert JSONAdapter.validate_python(datetime.now()) is not None