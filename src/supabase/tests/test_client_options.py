import dataclasses

import pytest
from supabase_auth import AsyncMemoryStorage, SyncMemoryStorage

from supabase import (
    AsyncClientOptions,
    AuthClientOptions,
    ClientOptions,
    FunctionsClientOptions,
    PostgrestClientOptions,
    RealtimeClientOptions,
    StorageClientOptions,
)


class TestClientOptions:
    async def test_replace_returns_updated_async_client_options(self) -> None:
        storage = AsyncMemoryStorage()
        await storage.set_item("key", "value")
        options = AsyncClientOptions(
            schema="schema",
            headers={"key": "value"},
            auto_refresh_token=False,
            persist_session=False,
            storage=storage,
        )

        actual = options.replace(schema="new schema")
        expected = AsyncClientOptions(
            schema="new schema",
            headers={"key": "value"},
            auto_refresh_token=False,
            persist_session=False,
            storage=storage,
        )

        assert actual == expected

    def test_replace_returns_updated_options(self) -> None:
        storage = SyncMemoryStorage()
        storage.set_item("key", "value")
        options = ClientOptions(
            schema="schema",
            headers={"key": "value"},
            auto_refresh_token=False,
            persist_session=False,
            storage=storage,
        )

        actual = options.replace(schema="new schema")
        assert actual
        expected = ClientOptions(
            schema="new schema",
            headers={"key": "value"},
            auto_refresh_token=False,
            persist_session=False,
            storage=storage,
        )

        assert actual == expected

    def test_replace_updates_only_new_options(self) -> None:
        # Arrange
        storage = SyncMemoryStorage()
        storage.set_item("key", "value")
        options = ClientOptions(storage=storage)
        new_options = options.replace()

        # Act
        new_options.storage.set_item("key", "new_value")

        # Assert
        assert options.storage.get_item("key") == "new_value"
        assert new_options.storage.get_item("key") == "new_value"

    def test_replace_honors_falsy_values(self) -> None:
        options = ClientOptions(headers={"key": "value"})

        actual = options.replace(
            auto_refresh_token=False, persist_session=False, headers={}
        )

        assert actual.auto_refresh_token is False
        assert actual.persist_session is False
        assert actual.headers == {}

    def test_replace_keeps_realtime_options(self) -> None:
        realtime = RealtimeClientOptions(heartbeat_interval=1)

        assert (
            ClientOptions(realtime=realtime).replace(schema="other").realtime
            == realtime
        )
        assert (
            AsyncClientOptions(realtime=realtime).replace(schema="other").realtime
            == realtime
        )

    def test_replace_updates_realtime_options(self) -> None:
        options = ClientOptions(realtime=RealtimeClientOptions(heartbeat_interval=1))
        realtime = RealtimeClientOptions(heartbeat_timeout=10)

        assert options.replace(realtime=realtime).realtime == realtime

    def test_realtime_options_default_to_realtime_defaults(self) -> None:
        assert ClientOptions().realtime == RealtimeClientOptions(
            heartbeat_interval=25, heartbeat_timeout=5
        )

    def test_realtime_options_accept_fractional_seconds(self) -> None:
        realtime = RealtimeClientOptions(heartbeat_interval=7.5, heartbeat_timeout=2.5)

        assert realtime.heartbeat_interval == 7.5
        assert realtime.heartbeat_timeout == 2.5

    @pytest.mark.parametrize(
        ("heartbeat_interval", "heartbeat_timeout", "message"),
        [
            (0, 5, "heartbeat_interval must be positive"),
            (25, -1, "heartbeat_timeout must be positive"),
            (float("nan"), 5, "heartbeat_interval must be positive"),
        ],
    )
    def test_realtime_options_reject_non_positive_durations(
        self, heartbeat_interval: float, heartbeat_timeout: float, message: str
    ) -> None:
        with pytest.raises(ValueError, match=message):
            RealtimeClientOptions(
                heartbeat_interval=heartbeat_interval,
                heartbeat_timeout=heartbeat_timeout,
            )

    def test_options_are_frozen(self) -> None:
        options = ClientOptions()

        with pytest.raises(dataclasses.FrozenInstanceError):
            options.schema = "other"  # pyrefly: ignore[read-only]

    def test_options_copy_the_given_headers(self) -> None:
        headers = {"key": "value"}
        options = ClientOptions(headers=headers)

        headers["key"] = "changed"

        assert options.headers == {"key": "value"}

    def test_request_timeouts_default_to_none(self) -> None:
        options = ClientOptions()

        assert options.request_timeout is None
        assert options.postgrest_options.request_timeout is None
        assert options.auth_options.request_timeout is None
        assert options.storage_options.request_timeout is None
        assert options.functions_options.request_timeout is None

    def test_replace_keeps_and_updates_request_timeouts(self) -> None:
        options = AsyncClientOptions(
            request_timeout=10,
            storage_options=StorageClientOptions(request_timeout=120),
        )

        kept = options.replace(schema="other")
        updated = options.replace(
            request_timeout=20,
            postgrest_options=PostgrestClientOptions(request_timeout=5),
            auth_options=AuthClientOptions(request_timeout=6),
            functions_options=FunctionsClientOptions(request_timeout=7),
        )

        assert kept.request_timeout == 10
        assert kept.storage_options.request_timeout == 120
        assert updated.request_timeout == 20
        assert updated.storage_options.request_timeout == 120
        assert updated.postgrest_options.request_timeout == 5
        assert updated.auth_options.request_timeout == 6
        assert updated.functions_options.request_timeout == 7

    def test_replace_clears_request_timeout_with_none(self) -> None:
        options = ClientOptions(request_timeout=10)

        assert options.replace(request_timeout=None).request_timeout is None

    @pytest.mark.parametrize(
        "options_class",
        [
            PostgrestClientOptions,
            AuthClientOptions,
            StorageClientOptions,
            FunctionsClientOptions,
            ClientOptions,
            AsyncClientOptions,
        ],
    )
    @pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf")])
    def test_request_timeout_must_be_positive(
        self, options_class: type, timeout: float
    ) -> None:
        with pytest.raises(ValueError, match="positive number of seconds"):
            options_class(request_timeout=timeout)
