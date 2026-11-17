"""
Defines the RealtimePresence class and its dependencies.
"""

from dataclasses import dataclass

from .types import (
    Presence,
    RawPresenceDiff,
    RawPresenceState,
    RealtimePresenceState,
)


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
    """
    Presences that joined under one key.

    ``current_presences`` holds the presences of the key before the change,
    and ``new_presences`` the presences that joined.
    """

    key: str
    current_presences: list[Presence]
    new_presences: list[Presence]


@dataclass
class PresenceLeave:
    """
    Presences that left one key.

    ``current_presences`` holds the presences of the key after the change, and
    ``left_presences`` the presences that left, as the presence state held them.
    """

    key: str
    current_presences: list[Presence]
    left_presences: list[Presence]


@dataclass
class PresenceSync:
    """
    The presence state changed. Read it with `RealtimeChannel.presence_state()`.
    """


PresenceEvent = PresenceJoin | PresenceLeave | PresenceSync


def _apply_diff(
    state: RealtimePresenceState, diff: RawPresenceDiff
) -> RealtimePresenceState:
    result = dict(state)
    for key, joined in _transform_state(diff.joins).items():
        by_ref = {presence.presence_ref: presence for presence in joined}
        held = [by_ref.pop(p.presence_ref, p) for p in result.get(key, [])]
        result[key] = held + list(by_ref.values())
    for key, left in _transform_state(diff.leaves).items():
        left_refs = {presence.presence_ref for presence in left}
        remaining = [p for p in result.get(key, []) if p.presence_ref not in left_refs]
        if remaining:
            result[key] = remaining
        else:
            result.pop(key, None)
    return result


def _changes(
    before: RealtimePresenceState, after: RealtimePresenceState
) -> list[PresenceEvent]:
    events: list[PresenceEvent] = []
    for key, presences in after.items():
        held = before.get(key, [])
        held_refs = {presence.presence_ref for presence in held}
        joined = [p for p in presences if p.presence_ref not in held_refs]
        if joined:
            events.append(PresenceJoin(key, list(held), joined))
    for key, presences in before.items():
        current = after.get(key, [])
        current_refs = {presence.presence_ref for presence in current}
        left = [p for p in presences if p.presence_ref not in current_refs]
        if left:
            events.append(PresenceLeave(key, list(current), left))
    events.append(PresenceSync())
    return events


class RealtimePresence:
    """
    The presence state of a channel, built from the ``presence_state`` and
    ``presence_diff`` messages of its current join.
    """

    def __init__(self) -> None:
        self.state: RealtimePresenceState = {}
        self._join_ref: str | None = None
        self._synced = False
        self._pending_diffs: list[RawPresenceDiff] = []

    def _on_join(self, join_ref: str) -> None:
        self._join_ref = join_ref
        self._synced = False
        self._pending_diffs = []

    def _is_from_another_join(self, join_ref: str | None) -> bool:
        return join_ref is not None and join_ref != self._join_ref

    def _on_state_event(
        self, payload: RawPresenceState, join_ref: str | None = None
    ) -> list[PresenceEvent]:
        if self._is_from_another_join(join_ref):
            return []
        state = _transform_state(payload)
        for diff in self._pending_diffs:
            state = _apply_diff(state, diff)
        self._pending_diffs = []
        self._synced = True
        return self._replace(state)

    def _on_diff_event(
        self, payload: RawPresenceDiff, join_ref: str | None = None
    ) -> list[PresenceEvent]:
        if self._is_from_another_join(join_ref):
            return []
        if not self._synced:
            self._pending_diffs.append(payload)
            return []
        return self._replace(_apply_diff(self.state, payload))

    def _on_unsubscribe(self) -> list[PresenceEvent]:
        was_joined = self._join_ref is not None
        self._join_ref = None
        self._synced = False
        self._pending_diffs = []
        if not was_joined and not self.state:
            return []
        return self._replace({})

    def _replace(self, state: RealtimePresenceState) -> list[PresenceEvent]:
        events = _changes(self.state, state)
        self.state = state
        return events
