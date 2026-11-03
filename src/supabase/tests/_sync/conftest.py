from typing import Iterable, Protocol

import pytest

from supabase import Client, ClientOptions
from supabase.httpx import create_client as create_httpx_client


def pytest_configure(config) -> None:
    from dotenv import load_dotenv

    load_dotenv(dotenv_path="tests/tests.env")


REST_URL = "http://127.0.0.1:3000"


def httpx(
    supabase_key: str, supabase_url: str, options: ClientOptions | None = None
) -> Client:
    return create_httpx_client(supabase_key, supabase_url, options=options)


class SyncClientCallable(Protocol):
    def __call__(
        self, supabase_key: str, supabase_url: str, options: ClientOptions | None = None
    ) -> Client: ...


@pytest.fixture(params=[httpx])
def create_client(
    request: pytest.FixtureRequest,
) -> Iterable[SyncClientCallable]:
    yield request.param  # just immediatly yield the `create_client` function
