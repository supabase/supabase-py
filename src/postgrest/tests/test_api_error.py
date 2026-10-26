from typing import Any

import pytest
from httpx import Client, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import HttpxSession

from postgrest import APIError, SyncPostgrestClient


@pytest.mark.parametrize(
    "body, message, details",
    [
        (b'{"message": "JWT expired"}', "JWT expired", None),
        (
            b'{"code": "PGRST201", "details": [{"x": 1}], "hint": null, "message": "m"}',
            "m",
            [{"x": 1}],
        ),
    ],
)
def test_response_error_json_missing_or_non_string_fields(
    body: bytes, message: str, details: Any
) -> None:
    def handler(request: Request) -> Response:
        return Response(400, content=body)

    with Client(transport=MockTransport(handler)) as http:
        client = SyncPostgrestClient(
            "https://example.com", http_session=HttpxSession(client=http)
        )
        with pytest.raises(APIError) as exc_info:
            client.from_("test").select("a").execute()

    assert exc_info.value.message == message
    assert exc_info.value.details == details
