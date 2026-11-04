"""
Defines the RealtimePresence class and its dependencies.
"""

import logging
from collections.abc import Generator
from dataclasses import dataclass

from .types import (
    Presence,
    RawPresenceDiff,
    RawPresenceState,
    RealtimePresenceState,
)

logger = logging.getLogger(__name__)


def _transform_state(
    state: RawPresenceState,
) -> RealtimePresenceState:
    """
    Transform the Phoenix presence state into a RealtimePresenceState.

    Each ``PresenceMeta`` becomes a ``Presence`` whose ``presence_ref`` is the
    meta's ``phx_ref``, even when the tracked state has its own
    ``presence_ref``. ``phx_ref_prev`` is dropped and every other field is kept
    as an extra field on the ``Presence``.
    """
    return {
        key: [
            Presence.model_validate(
                {**(meta.model_extra or {}), "presence_ref": meta.phx_ref}
            )
            for meta in entry.metas
        ]
        for key, entry in state.items()
    }


@dataclass
class PresenceJoin:
    key: str
    current_presences: list[Presence]
    new_presences: list[Presence]


@dataclass
class PresenceLeave:
    key: str
    current_presences: list[Presence]
    left_presences: list[Presence]


PresenceEvent = PresenceJoin | PresenceLeave


class RealtimePresence:
    def __init__(self) -> None:
        self.state: RealtimePresenceState = {}

    def _on_state_event(
        self, payload: RawPresenceState
    ) -> Generator[PresenceEvent, None, None]:
        state = _transform_state(payload)
        self.state = yield from self._sync_state(state)

    def _on_diff_event(
        self, payload: RawPresenceDiff
    ) -> Generator[PresenceEvent, None, None]:
        joins = _transform_state(payload.joins)
        leaves = _transform_state(payload.leaves)
        self.state = yield from self._sync_diff(joins, leaves)

    def _sync_state(
        self,
        new_state: RealtimePresenceState,
    ) -> Generator[PresenceEvent, None, RealtimePresenceState]:
        leaves = {k: v for k, v in self.state.items() if k not in new_state}

        for key, value in new_state.items():
            new_presence_refs = {presence.presence_ref for presence in value}
            left_presences = [
                presence
                for presence in self.state.get(key, [])
                if presence.presence_ref not in new_presence_refs
            ]
            if left_presences:
                leaves[key] = left_presences

        res = yield from self._sync_diff(new_state, leaves)
        return res

    def _sync_diff(
        self, joins: RealtimePresenceState, leaves: RealtimePresenceState
    ) -> Generator[PresenceEvent, None, RealtimePresenceState]:
        for key, joined_presences in joins.items():
            current_presences = self.state.get(key, [])
            current_presence_refs = {
                presence.presence_ref for presence in current_presences
            }
            new_presences = [
                presence
                for presence in joined_presences
                if presence.presence_ref not in current_presence_refs
            ]
            joined_presence_refs = {
                presence.presence_ref for presence in joined_presences
            }
            self.state[key] = [
                presence
                for presence in current_presences
                if presence.presence_ref not in joined_presence_refs
            ] + joined_presences
            if new_presences:
                yield PresenceJoin(key, current_presences, new_presences)

        for key, left_presences in leaves.items():
            current_presences = self.state.get(key, [])
            current_presence_refs = {
                presence.presence_ref for presence in current_presences
            }
            left_presences = [
                presence
                for presence in left_presences
                if presence.presence_ref in current_presence_refs
            ]
            if not left_presences:
                continue

            presence_refs_to_remove = {
                presence.presence_ref for presence in left_presences
            }
            current_presences = [
                presence
                for presence in current_presences
                if presence.presence_ref not in presence_refs_to_remove
            ]
            if current_presences:
                self.state[key] = current_presences
            else:
                del self.state[key]
            yield PresenceLeave(key, current_presences, left_presences)

        return self.state
