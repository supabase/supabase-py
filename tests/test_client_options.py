from gotrue import SyncMemoryStorage

from supabase.lib.client_options import ClientOptions


def test__client_options__replace__returns_updated_options():
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
    expected = ClientOptions(
        schema="new schema",
        headers={"key": "value"},
        auto_refresh_token=False,
        persist_session=False,
        storage=storage,
        realtime={"key": "value"},
    )

    assert actual == expected


def test__client_options__replace__updates_only_new_options():
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
