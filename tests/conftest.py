from __future__ import annotations

import os

import pytest

from supabase_py import Client, create_client


@pytest.fixture(scope="function")
def supabase() -> Client:
    url: str = os.environ.get("SUPABASE_TEST_URL")
    key: str = os.environ.get("SUPABASE_TEST_KEY")
    supabase: Client = create_client(url, key)
    return supabase
