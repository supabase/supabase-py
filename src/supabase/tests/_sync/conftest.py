from typing import Any, Protocol

import pytest

from supabase import Client
from supabase.httpx import create_client as create_httpx_client


def pytest_configure(config: pytest.Config) -> None:
    from dotenv import load_dotenv

    load_dotenv(dotenv_path="tests/tests.env")


REST_URL = "http://127.0.0.1:3000"


def httpx(supabase_url: str, supabase_key: str, **kwargs: Any) -> Client:
    return create_httpx_client(supabase_url, supabase_key, **kwargs)


class SyncClientCallable(Protocol):
    def __call__(
        self, supabase_url: str, supabase_key: str, **kwargs: Any
    ) -> Client: ...


@pytest.fixture(params=[httpx])
def create_client(
    request: pytest.FixtureRequest,
) -> SyncClientCallable:
    client_factory: SyncClientCallable = request.param
    return client_factory
