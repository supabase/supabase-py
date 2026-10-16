from typing import Any

import pytest
from httpx import Client
from supabase_utils.http.adapters.httpx import HttpxSession

from postgrest import SyncPostgrestClient


@pytest.mark.parametrize("head", [False, True])
def test_rpc_query_params_send_lists_as_array_literals(head: bool) -> None:
    with Client() as http:
        client = SyncPostgrestClient(
            "https://example.com", http_session=HttpxSession(client=http)
        )
        params: Any = {"ids": [1, 2, 3], "name": "x"}
        builder = client.rpc("sum_ids", params, head=head, get=not head)

        assert builder.request.query.get_list("ids") == ["{1,2,3}"]
        assert builder.request.query["name"] == "x"
