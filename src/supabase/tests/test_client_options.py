from supabase_auth import AsyncMemoryStorage, SyncMemoryStorage

from supabase import AsyncClientOptions, ClientOptions, RealtimeClientOptions


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
