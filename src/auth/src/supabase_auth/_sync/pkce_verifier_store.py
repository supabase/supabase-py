from __future__ import annotations

import json
from threading import Lock
from typing import List, Optional

from ..constants import PKCE_MAX_CONCURRENT_FLOWS
from ..helpers import (
    pkce_flow_index_key,
    pkce_legacy_verifier_key,
    pkce_verifier_slot_key,
    validate_pkce_flow_id,
)
from .storage import SyncSupportedStorage


class SyncPKCEVerifierStore:
    """Keeps one PKCE code verifier per pending flow.

    Each flow gets its own storage slot keyed by a flow id, so starting a
    second PKCE flow no longer overwrites the verifier of the first one. The
    store is bounded: an ordered index of pending flow ids is kept in storage
    (storage backends cannot enumerate keys) and the oldest flow is evicted
    once more than ``PKCE_MAX_CONCURRENT_FLOWS`` are pending.

    The single legacy key (``{storage_key}-code-verifier``) is still written
    with the verifier of the most recently started flow and is used whenever a
    caller does not know its flow id, which keeps older call sites working.
    """

    def __init__(self, storage: SyncSupportedStorage, storage_key: str) -> None:
        self._storage = storage
        self._storage_key = storage_key
        # The index is read, modified and written back across several awaits;
        # without serialization two concurrent flow starts could each write a
        # different index and one slot would become unreachable for eviction
        # and clean-up.
        self._lock = Lock()

    @property
    def legacy_key(self) -> str:
        return pkce_legacy_verifier_key(self._storage_key)

    @property
    def index_key(self) -> str:
        return pkce_flow_index_key(self._storage_key)

    def slot_key(self, flow_id: str) -> str:
        return pkce_verifier_slot_key(self._storage_key, flow_id)

    def _read_index(self) -> List[str]:
        raw = self._storage.get_item(self.index_key)
        if not raw:
            return []
        try:
            parsed = json.loads(raw)
        except ValueError:
            return []
        if not isinstance(parsed, list):
            return []
        # Ids read back from storage are as untrusted as caller input.
        return [
            flow_id
            for flow_id in (validate_pkce_flow_id(item) for item in parsed)
            if flow_id is not None
        ]

    def _write_index(self, index: List[str]) -> None:
        if index:
            self._storage.set_item(self.index_key, json.dumps(index))
        else:
            self._storage.remove_item(self.index_key)

    def store(self, flow_id: str, code_verifier: str) -> List[str]:
        """Store ``code_verifier`` for ``flow_id`` and return any evicted flow ids.

        Raises ``ValueError`` for a malformed flow id: a slot the index could
        not validate on the way back out could never be evicted or removed.
        """
        if validate_pkce_flow_id(flow_id) is None:
            raise ValueError("Invalid PKCE flow id")

        with self._lock:
            self._storage.set_item(self.slot_key(flow_id), code_verifier)

            index = [item for item in self._read_index() if item != flow_id]
            index.append(flow_id)
            evicted: List[str] = []
            while len(index) > PKCE_MAX_CONCURRENT_FLOWS:
                oldest = index.pop(0)
                self._storage.remove_item(self.slot_key(oldest))
                evicted.append(oldest)
            self._write_index(index)

            # Mirror the newest verifier into the legacy key for callers that
            # never learned their flow id.
            self._storage.set_item(self.legacy_key, code_verifier)
            return evicted

    def retrieve(self, flow_id: Optional[str]) -> Optional[str]:
        """Return the verifier for ``flow_id``, or the legacy verifier if it is ``None``.

        With a flow id only that flow's slot is consulted. Falling back to
        another flow's verifier would spend the single-use auth code on a
        request that cannot succeed, so a miss is reported as ``None`` instead.
        """
        if flow_id is None:
            return self._storage.get_item(self.legacy_key)
        if validate_pkce_flow_id(flow_id) is None:
            return None
        return self._storage.get_item(self.slot_key(flow_id))

    def remove(self, flow_id: Optional[str]) -> None:
        """Forget the verifier of ``flow_id``, or only the legacy verifier if it is ``None``.

        The legacy key is cleared alongside a slot only when it still holds
        that slot's verifier, so removing a finished flow never destroys the
        fallback of a newer pending flow.
        """
        with self._lock:
            if flow_id is None:
                self._storage.remove_item(self.legacy_key)
                return
            if validate_pkce_flow_id(flow_id) is None:
                return

            slot_key = self.slot_key(flow_id)
            removed_verifier = self._storage.get_item(slot_key)
            self._storage.remove_item(slot_key)

            index = self._read_index()
            remaining = [item for item in index if item != flow_id]
            if len(remaining) != len(index):
                self._write_index(remaining)

            if removed_verifier is not None:
                legacy_verifier = self._storage.get_item(self.legacy_key)
                if legacy_verifier == removed_verifier:
                    self._storage.remove_item(self.legacy_key)

    def remove_all(self) -> None:
        """Forget every pending verifier, the index and the legacy verifier."""
        with self._lock:
            for flow_id in self._read_index():
                self._storage.remove_item(self.slot_key(flow_id))
            self._storage.remove_item(self.index_key)
            self._storage.remove_item(self.legacy_key)
