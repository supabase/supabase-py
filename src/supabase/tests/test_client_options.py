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

    def test_replace_accepts_falsy_values_for_async_options(self) -> None:
        options = AClientOptions(
            auto_refresh_token=True,
            persist_session=True,
            postgrest_client_timeout=5,
            storage_client_timeout=5,
            function_client_timeout=5,
            headers={"x-app-name": "apple"},
        )

        actual = options.replace(
            auto_refresh_token=False,
            persist_session=False,
            postgrest_client_timeout=0,
            storage_client_timeout=0,
            function_client_timeout=0,
            headers={},
        )

        assert actual.auto_refresh_token is False
        assert actual.persist_session is False
        assert actual.postgrest_client_timeout == 0
        assert actual.storage_client_timeout == 0
        assert actual.function_client_timeout == 0
        assert actual.headers == {}

    def test_replace_accepts_falsy_values_for_sync_options(self) -> None:
        options = ClientOptions(
            auto_refresh_token=True,
            persist_session=True,
            postgrest_client_timeout=5,
            storage_client_timeout=5,
            function_client_timeout=5,
            headers={"x-app-name": "apple"},
        )

        actual = options.replace(
            auto_refresh_token=False,
            persist_session=False,
            postgrest_client_timeout=0,
            storage_client_timeout=0,
            function_client_timeout=0,
            headers={},
        )

        assert actual.auto_refresh_token is False
        assert actual.persist_session is False
        assert actual.postgrest_client_timeout == 0
        assert actual.storage_client_timeout == 0
        assert actual.function_client_timeout == 0
        assert actual.headers == {}

    def test_async_replace_copies_headers_and_preserves_function_timeout(self) -> None:
        options = AClientOptions(
            headers={"x-app-name": "apple"},
            function_client_timeout=9,
        )

        replaced = options.replace(schema="new_schema")
        replaced.headers["x-app-name"] = "grapes"

        assert options.headers["x-app-name"] == "apple"
        assert replaced.function_client_timeout == 9
        assert options.replace(function_client_timeout=1).function_client_timeout == 1

    def test_sync_replace_copies_headers_and_preserves_function_timeout(self) -> None:
        options = ClientOptions(
            headers={"x-app-name": "apple"},
            function_client_timeout=9,
        )

        replaced = options.replace(schema="new_schema")
        replaced.headers["x-app-name"] = "grapes"

        assert options.headers["x-app-name"] == "apple"
        assert replaced.function_client_timeout == 9
        assert options.replace(function_client_timeout=1).function_client_timeout == 1
