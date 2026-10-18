import asyncio
import json

from supabase_auth import AsyncMemoryStorage
from supabase_auth._async.pkce_verifier_store import AsyncPKCEVerifierStore
from supabase_auth.constants import PKCE_MAX_CONCURRENT_FLOWS


async def test_concurrent_stores_preserve_the_bound_and_index_every_flow() -> None:
    """Interleaved flow starts must not lose index entries.

    The index is read, modified and written back across awaits; without
    serialization two starts could each write a different index and leave a
    slot that can never be evicted or cleaned up.
    """
    storage = AsyncMemoryStorage()
    store = AsyncPKCEVerifierStore(storage, "test-storage-key")
    flow_ids = [f"flow-id-{i:08d}" for i in range(20)]

    await asyncio.gather(
        *(store.store(flow_id, f"verifier-{flow_id}") for flow_id in flow_ids)
    )

    slot_keys = [key for key in storage.storage if "-flow-" in key]
    index = json.loads(storage.storage[store.index_key])

    assert len(slot_keys) == PKCE_MAX_CONCURRENT_FLOWS
    assert len(index) == PKCE_MAX_CONCURRENT_FLOWS
    # every surviving slot is reachable through the index
    assert sorted(store.slot_key(flow_id) for flow_id in index) == sorted(slot_keys)

    await store.remove_all()
    assert storage.storage == {}
