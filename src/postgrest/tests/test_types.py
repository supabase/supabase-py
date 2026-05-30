from datetime import datetime,date,time
from uuid import UUID

from postgrest.types import JSONAdapter

def test_json_adapter():
    assert JSONAdapter.validate_python(None) is None
    assert JSONAdapter.validate_python(UUID("12345678-1234-5678-1234-567812345678")) is not None
    assert JSONAdapter.validate_python(datetime.now()) is not None
    assert JSONAdapter.validate_python(date.today()) is not None
    assert JSONAdapter.validate_python(time()) is not None