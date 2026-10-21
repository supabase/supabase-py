"""
Defines the RealtimePresence class and its dependencies.
"""

import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, Generator, List, Optional, Union

from .types import (
    Presence,
    PresenceDiff,
    PresenceEvents,
    PresenceOpts,
    RawPresenceDiff,
    RawPresenceState,
    RealtimePresenceState,
)

logger = logging.getLogger(__name__)


def _transform_state(
    state: RawPresenceState,
) -> RealtimePresenceState:
    """
    Transform the raw presence state into a standardized RealtimePresenceState format.

    This method processes the input state, which can be either a RawPresenceState or
    an already transformed RealtimePresenceState. It handles the conversion of the
    Phoenix channel's presence format to our internal representation.

    Args:
        state RawPresenceState: The presence state to transform.

    Returns:
        RealtimePresenceState: The transformed presence state.

    Example:
        Input (RawPresenceState):
        {
            "user1": {
                "metas": [
                    {"phx_ref": "ABC123", "user_id": "user1", "status": "online"},
                    {"phx_ref": "DEF456", "phx_ref_prev": "ABC123", "user_id": "user1", "status": "away"}
                ]
            },
            "user2": [{"user_id": "user2", "status": "offline"}]
        }

        Output (RealtimePresenceState):
        {
            "user1": [
                {"presence_ref": "ABC123", "user_id": "user1", "status": "online"},
                {"presence_ref": "DEF456", "user_id": "user1", "status": "away"}
            ],
            "user2": [{"user_id": "user2", "status": "offline"}]
        }
    """
    new_state: RealtimePresenceState = {}
    for key, presences in state.items():
        new_state[key] = []

        for presence in presences["metas"]:
            if "phx_ref_prev" in presence:
                del presence["phx_ref_prev"]
            new_presence: Presence = {"presence_ref": presence.pop("phx_ref")}
            new_presence.update(presence)
            new_state[key].append(new_presence)
    return new_state


@dataclass
class PresenceJoin:
    key: str
    current_presences: List[Presence]
    new_presences: List[Presence]


@dataclass
class PresenceLeave:
    key: str
    current_presences: List[Presence]
    left_presences: List[Presence]


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
        joins = _transform_state(payload["joins"])
        leaves = _transform_state(payload["leaves"])
        self.state = yield from self._sync_diff(joins, leaves)

    def _sync_state(
        self,
        new_state: RealtimePresenceState,
    ) -> Generator[PresenceEvent, None, RealtimePresenceState]:
        leaves = {k: v for k, v in self.state.items() if k not in new_state}

        for key, value in new_state.items():
            new_presence_refs = {presence["presence_ref"] for presence in value}
            left_presences = [
                presence
                for presence in self.state.get(key, [])
                if presence["presence_ref"] not in new_presence_refs
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
                presence["presence_ref"] for presence in current_presences
            }
            new_presences = [
                presence
                for presence in joined_presences
                if presence["presence_ref"] not in current_presence_refs
            ]
            joined_presence_refs = {
                presence["presence_ref"] for presence in joined_presences
            }
            self.state[key] = joined_presences + [
                presence
                for presence in current_presences
                if presence["presence_ref"] not in joined_presence_refs
            ]
            if new_presences:
                yield PresenceJoin(key, current_presences, new_presences)

        for key, left_presences in leaves.items():
            current_presences = self.state.get(key, [])
            current_presence_refs = {
                presence["presence_ref"] for presence in current_presences
            }
            left_presences = [
                presence
                for presence in left_presences
                if presence["presence_ref"] in current_presence_refs
            ]
            if not left_presences:
                continue

            presence_refs_to_remove = {
                presence["presence_ref"] for presence in left_presences
            }
            current_presences = [
                presence
                for presence in current_presences
                if presence["presence_ref"] not in presence_refs_to_remove
            ]
            if current_presences:
                self.state[key] = current_presences
            else:
                del self.state[key]
            yield PresenceLeave(key, current_presences, left_presences)

        return self.state
