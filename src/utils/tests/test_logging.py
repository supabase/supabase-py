import logging
from collections.abc import Iterator

import pytest
from supabase_utils import _logging
from supabase_utils.http.errors import SupabaseTransportError
from supabase_utils.http.headers import Headers
from supabase_utils.http.io import AsyncHttpIO, HttpMethod, SyncHttpIO
from supabase_utils.http.query import URLQuery
from supabase_utils.http.request import JSONRequest
from supabase_utils.http.retry import RetryPolicy
from yarl import URL

from .test_io import AsyncFakeSession, FakeSession

BASE_URL = URL("https://example.com/rest/v1")
SECRETS = ("secret-api-key", "secret-jwt", "secret-query", "secret-body")
HEADERS = Headers.from_mapping(
    {"apikey": "secret-api-key", "Authorization": "Bearer secret-jwt"}
)


def create_item() -> HttpMethod[int]:
    response = yield JSONRequest(
        path=["items"],
        method="POST",
        body={"password": "secret-body"},
        query=URLQuery.from_mapping({"token": "secret-query"}),
        retry=True,
    )
    return response.status


def http_logs(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [
        record.getMessage()
        for record in caplog.records
        if record.name == "supabase.http"
    ]


def assert_no_secrets(caplog: pytest.LogCaptureFixture) -> None:
    for secret in SECRETS:
        assert secret not in caplog.text
        for record in caplog.records:
            assert secret not in record.getMessage()


def test_sync_requests_are_logged_without_secrets(
    caplog: pytest.LogCaptureFixture,
) -> None:
    executor = SyncHttpIO(
        FakeSession([503, 201]), retry=RetryPolicy(base_delay=0, jitter=0)
    )
    with caplog.at_level(logging.DEBUG, logger="supabase"):
        assert executor.communicate(BASE_URL, HEADERS, create_item()) == 201

    logs = http_logs(caplog)
    assert len(logs) == 3
    assert logs[0].startswith("POST /rest/v1/items 503 in ")
    assert logs[1].startswith("POST /rest/v1/items failed, retry 1 of ")
    assert logs[2].startswith("POST /rest/v1/items 201 in ")
    assert logs[2].endswith(" milliseconds")
    assert all(record.levelno == logging.DEBUG for record in caplog.records)
    assert_no_secrets(caplog)


async def test_async_requests_are_logged_without_secrets(
    caplog: pytest.LogCaptureFixture,
) -> None:
    executor = AsyncHttpIO(
        AsyncFakeSession([SupabaseTransportError, 201]),
        retry=RetryPolicy(base_delay=0, jitter=0),
    )
    with caplog.at_level(logging.DEBUG, logger="supabase"):
        assert await executor.communicate(BASE_URL, HEADERS, create_item()) == 201

    logs = http_logs(caplog)
    assert logs[0].startswith("POST /rest/v1/items failed in ")
    assert logs[0].endswith(" milliseconds with SupabaseTransportError")
    assert logs[-1].startswith("POST /rest/v1/items 201 in ")
    assert_no_secrets(caplog)


def test_requests_are_not_logged_above_debug(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.INFO, logger="supabase"):
        SyncHttpIO(FakeSession([201])).communicate(BASE_URL, HEADERS, create_item())

    assert caplog.records == []


def test_the_supabase_logger_has_a_null_handler() -> None:
    root = logging.getLogger("supabase")
    assert any(isinstance(handler, logging.NullHandler) for handler in root.handlers)
    assert _logging.get_logger("http").parent is root


@pytest.fixture
def root_logger() -> Iterator[logging.Logger]:
    root = logging.getLogger("supabase")
    handlers, level = list(root.handlers), root.level
    yield root
    root.handlers = handlers
    root.setLevel(level)


@pytest.mark.parametrize(
    ("value", "level"),
    [("debug", logging.DEBUG), ("INFO", logging.INFO), (" warn ", logging.WARNING)],
)
def test_supabase_log_prints_the_supabase_logs(
    monkeypatch: pytest.MonkeyPatch,
    root_logger: logging.Logger,
    value: str,
    level: int,
) -> None:
    monkeypatch.setenv("SUPABASE_LOG", value)
    root_logger.handlers = []
    _logging._configure_root_logger()

    assert root_logger.level == level
    assert [type(handler) for handler in root_logger.handlers] == [
        logging.NullHandler,
        logging.StreamHandler,
    ]


@pytest.mark.parametrize("value", ["", "verbose"])
def test_supabase_log_without_a_level_prints_nothing(
    monkeypatch: pytest.MonkeyPatch, root_logger: logging.Logger, value: str
) -> None:
    monkeypatch.setenv("SUPABASE_LOG", value)
    root_logger.handlers = []
    root_logger.setLevel(logging.NOTSET)
    _logging._configure_root_logger()

    assert root_logger.level == logging.NOTSET
    assert [type(handler) for handler in root_logger.handlers] == [logging.NullHandler]
