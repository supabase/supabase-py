from supabase_auth import SyncMemoryStorage

from supabase import AClientOptions, ClientOptions


class TestClientOptions:
    def test_replace_returns_updated_aclient_options(self):
        storage = SyncMemoryStorage()
        storage.set_item("key", "value")
        options = AClientOptions(
            schema="schema",
            headers={"key": "value"},
            auto_refresh_token=False,
            persist_session=False,
            storage=storage,
            realtime={"key": "value"},
        )

        actual = options.replace(schema="new schema")
        expected = AClientOptions(
            schema="new schema",
            headers={"key": "value"},
            auto_refresh_token=False,
            persist_session=False,
            storage=storage,
            realtime={"key": "value"},
        )

        assert actual == expected

    def test_replace_returns_updated_options(self):
        storage = SyncMemoryStorage()
        storage.set_item("key", "value")
        options = ClientOptions(
            schema="schema",
            headers={"key": "value"},
            auto_refresh_token=False,
            persist_session=False,
            storage=storage,
            realtime={"key": "value"},
        )

        actual = options.replace(schema="new schema")
        assert actual
        expected = ClientOptions(
            schema="new schema",
            headers={"key": "value"},
            auto_refresh_token=False,
            persist_session=False,
            storage=storage,
            realtime={"key": "value"},
        )

        assert actual == expected

    def test_replace_updates_only_new_options(self):
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
