from __future__ import annotations

from typing import Any

import pytest


def test_new_timeout_configuration():
    from supabase import create_client, Client
    from supabase.lib.client_options import ClientOptions
    import os

    url: str = os.environ.get("SUPABASE_TEST_URL")
    key: str = os.environ.get("SUPABASE_TEST_KEY")

    client = create_client(url, key)  # No options used here.
    data   = [{"item": value} for value in range(0, 1000000)]

    client.table("sample").insert(data).execute()


@pytest.mark.xfail(
    reason="postgrest client timeout reached before processing the request."
)
def test_passing_wrong_timeout_value():
    from supabase import create_client, Client
    from supabase.lib.client_options import ClientOptions
    import os

    url: str = os.environ.get("SUPABASE_TEST_URL")
    key: str = os.environ.get("SUPABASE_TEST_KEY")

    options = ClientOptions(postgrest_client_timeout = 5)  # Explicit timeout.
    client  = create_client(url, key, options)
    data    = [{"item": value} for value in range(0, 1000000)]

    client.table("sample").insert(data).execute()
