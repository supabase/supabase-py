from supabase_auth import AsyncMemoryStorage, SyncMemoryStorage

from supabase import AClientOptions, ClientOptions


class TestClientOptions:
    async def test_replace_returns_updated_aclient_options(self) -> None:
        storage = AsyncMemoryStorage()
        await storage.set_item("key", "value")
        options = AClientOptions(
            schema="schema",
            headers={"key": "value"},
            auto_refresh_token=False,
            persist_session=False,
            storage=storage,
        )

        actual = options.replace(schema="new schema")
        expected = AClientOptions(
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
        options = ClientOptions(headers={"key": "value"}, realtime={"hb_interval": 1})

        actual = options.replace(
            auto_refresh_token=False, persist_session=False, headers={}, realtime={}
        )

        assert actual.auto_refresh_token is False
        assert actual.persist_session is False
        assert actual.headers == {}
        assert actual.realtime == {}

    def test_replace_keeps_realtime_options(self) -> None:
        options = ClientOptions(realtime={"hb_interval": 1})

        assert options.replace(schema="other").realtime == {"hb_interval": 1}
        assert AClientOptions(realtime={"hb_interval": 1}).replace(
            schema="other"
        ).realtime == {"hb_interval": 1}
