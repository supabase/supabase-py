import json
import re

import pytest
from supabase_auth import SyncMemoryStorage
from supabase_auth.constants import PKCE_MAX_CONCURRENT_FLOWS

from .clients import auth_client


def _slot_keys(storage: dict) -> list:
    return sorted(key for key in storage if "-flow-" in key)


def _store() -> tuple:
    """A verifier store bound to a fresh in-memory storage."""
    client = auth_client()
    storage = client._storage
    assert isinstance(storage, SyncMemoryStorage)
    return client._pkce_verifier_store, storage.storage


def test_store_keeps_one_slot_per_flow_plus_legacy_key() -> None:
    store, storage = _store()

    store.store("flow-id-aaaaaaaa", "verifier-a")
    store.store("flow-id-bbbbbbbb", "verifier-b")

    assert storage[store.slot_key("flow-id-aaaaaaaa")] == "verifier-a"
    assert storage[store.slot_key("flow-id-bbbbbbbb")] == "verifier-b"
    # the legacy key mirrors the most recently started flow
    assert storage[store.legacy_key] == "verifier-b"
    assert json.loads(storage[store.index_key]) == [
        "flow-id-aaaaaaaa",
        "flow-id-bbbbbbbb",
    ]


def test_store_evicts_oldest_flow_beyond_bound_and_reports_it() -> None:
    store, storage = _store()
    flow_ids = [f"flow-id-{i:08d}" for i in range(PKCE_MAX_CONCURRENT_FLOWS + 1)]

    evicted = []
    for flow_id in flow_ids:
        evicted.extend(store.store(flow_id, f"verifier-{flow_id}"))

    assert evicted == [flow_ids[0]]
    assert store.slot_key(flow_ids[0]) not in storage
    assert json.loads(storage[store.index_key]) == flow_ids[1:]
    assert len(_slot_keys(storage)) == PKCE_MAX_CONCURRENT_FLOWS


def test_store_same_flow_again_does_not_consume_another_slot() -> None:
    store, storage = _store()

    store.store("flow-id-aaaaaaaa", "verifier-a1")
    store.store("flow-id-bbbbbbbb", "verifier-b")
    store.store("flow-id-aaaaaaaa", "verifier-a2")

    assert storage[store.slot_key("flow-id-aaaaaaaa")] == "verifier-a2"
    assert len(_slot_keys(storage)) == 2
    # re-storing moves the flow to the newest position
    assert json.loads(storage[store.index_key]) == [
        "flow-id-bbbbbbbb",
        "flow-id-aaaaaaaa",
    ]


def test_store_rejects_flow_id_it_could_not_evict_later() -> None:
    store, storage = _store()

    with pytest.raises(ValueError):
        store.store("slash/../evil", "verifier")

    assert storage == {}


def test_store_tolerates_corrupt_or_hostile_index() -> None:
    store, storage = _store()

    for raw_index in [
        "not-json{",
        '{"a": 1}',
        '[42, null, "short", "../etc/passwd", "ok_flow-id"]',
    ]:
        storage[store.index_key] = raw_index
        store.store("flow-id-aaaaaaaa", "verifier-a")

        index = json.loads(storage[store.index_key])
        assert index[-1] == "flow-id-aaaaaaaa"
        assert all(re.match(r"^[a-zA-Z0-9_-]{8,64}$", item) for item in index)


def test_retrieve_is_slot_only_when_flow_id_is_given() -> None:
    store, _ = _store()
    store.store("flow-id-aaaaaaaa", "verifier-a")
    store.store("flow-id-bbbbbbbb", "verifier-b")

    assert store.retrieve("flow-id-aaaaaaaa") == "verifier-a"
    # an unknown flow must not borrow another flow's verifier
    assert store.retrieve("flow-id-gone0000") is None
    assert store.retrieve("slash/../evil") is None
    # without a flow id the legacy (most recent) verifier is used
    assert store.retrieve(None) == "verifier-b"


def test_remove_only_touches_its_own_flow() -> None:
    store, storage = _store()
    store.store("flow-id-aaaaaaaa", "verifier-a")
    store.store("flow-id-bbbbbbbb", "verifier-b")

    store.remove("flow-id-aaaaaaaa")

    assert store.slot_key("flow-id-aaaaaaaa") not in storage
    assert storage[store.slot_key("flow-id-bbbbbbbb")] == "verifier-b"
    # the legacy key belongs to flow b and survives
    assert storage[store.legacy_key] == "verifier-b"
    assert json.loads(storage[store.index_key]) == ["flow-id-bbbbbbbb"]


def test_remove_drops_legacy_key_when_it_belongs_to_removed_flow() -> None:
    store, storage = _store()
    store.store("flow-id-aaaaaaaa", "verifier-a")
    store.store("flow-id-bbbbbbbb", "verifier-b")

    store.remove("flow-id-bbbbbbbb")

    assert store.legacy_key not in storage
    assert storage[store.slot_key("flow-id-aaaaaaaa")] == "verifier-a"
    assert json.loads(storage[store.index_key]) == ["flow-id-aaaaaaaa"]


def test_remove_without_flow_id_only_touches_legacy_key() -> None:
    store, storage = _store()
    store.store("flow-id-aaaaaaaa", "verifier-a")
    store.store("flow-id-bbbbbbbb", "verifier-b")

    store.remove(None)

    assert store.legacy_key not in storage
    assert len(_slot_keys(storage)) == 2
    assert json.loads(storage[store.index_key]) == [
        "flow-id-aaaaaaaa",
        "flow-id-bbbbbbbb",
    ]


def test_remove_unknown_flow_leaves_index_untouched() -> None:
    store, storage = _store()
    store.store("flow-id-aaaaaaaa", "verifier-a")
    before = dict(storage)

    store.remove("flow-id-gone0000")

    assert storage == before


def test_remove_all_clears_every_slot_the_index_and_legacy_key() -> None:
    store, storage = _store()
    store.store("flow-id-aaaaaaaa", "verifier-a")
    store.store("flow-id-bbbbbbbb", "verifier-b")

    store.remove_all()

    assert storage == {}


def test_keys_end_in_code_verifier_and_contain_no_dot() -> None:
    store, _ = _store()
    # the default storage key itself contains dots; only the suffix we add must not
    prefix = store._storage_key
    for key in [
        store.slot_key("flow-id-aaaaaaaa"),
        store.index_key,
        store.legacy_key,
    ]:
        assert key.startswith(prefix)
        assert key.endswith("-code-verifier")
        assert "." not in key[len(prefix) :]
