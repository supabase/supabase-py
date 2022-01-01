from gotrue import SyncMemoryStorage

from supabase.lib.client_options import ClientOptions


def test__client_options__replace__returns_updated_options():
    local_storage = SyncMemoryStorage()
    local_storage.set_item("key", "value")
    options = ClientOptions(
        schema="schema",
        headers={"key": "value"},
        auto_refresh_token=False,
        persist_session=False,
        local_storage=local_storage,
        realtime={"key": "value"},
    )

    actual = options.replace(schema="new schema")
    expected = ClientOptions(
        schema="new schema",
        headers={"key": "value"},
        auto_refresh_token=False,
        persist_session=False,
        local_storage=local_storage,
        realtime={"key": "value"},
    )

    assert actual == expected


def test__client_options__replace__updates_only_new_options():
    # Arrange
    local_storage = SyncMemoryStorage()
    local_storage.set_item("key", "value")
    options = ClientOptions(local_storage=local_storage)
    new_options = options.replace()

    # Act
    new_options.local_storage.set_item("key", "new_value")

    # Assert
    assert options.local_storage.get_item("key") == "new_value"
    assert new_options.local_storage.get_item("key") == "new_value"
