from __future__ import annotations

import os

import pytest

from supabase import Client, create_client


@pytest.fixture(scope="session")
def supabase() -> Client:
    url = os.environ.get("SUPABASE_TEST_URL")
    assert url is not None, "Must provide SUPABASE_TEST_URL environment variable"
    key = os.environ.get("SUPABASE_TEST_KEY")
    assert key is not None, "Must provide SUPABASE_TEST_KEY environment variable"
    supabase: Client = create_client(url, key)
    return supabase
