from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Mapping, Optional

from typing_extensions import assert_never, overload

from ..message import Message, ReplyPostgresChanges
from ..types import DEFAULT_TIMEOUT, Callback, RealtimeAcknowledgementStatus, _Hook

if TYPE_CHECKING:
    from .channel import AsyncRealtimeChannel

logger = logging.getLogger(__name__)


class AsyncPush:
    def __init__(
        self,
        channel: AsyncRealtimeChannel,
        event: str,
        payload: Optional[Mapping[str, Any]] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        self.channel = channel
        self.event = event
        self.payload = payload or {}
        self.timeout = timeout
        self.rec_hooks: List[_Hook] = []
        self.ref: Optional[str] = None
        self.received_resp: Optional[
            tuple[RealtimeAcknowledgementStatus, Dict[str, Any]]
        ] = None
        self.sent = False
        self.timeout_task: Optional[asyncio.Task] = None
        self.ok_callbacks: list[Callback[[ReplyPostgresChanges], None]] = []
        self.error_callbacks: list[Callback[[Dict[str, Any]], None]] = []
        self.timeout_callbacks: list[Callback[[], None]] = []

    async def resend(self):
        self.ref = None
        self.received_resp = None
        self.sent = False
        await self.send()

    async def send(self):
        if (
            self.received_resp
            and self.received_resp[0] == RealtimeAcknowledgementStatus.Timeout
        ):
            return

        self.ref = self.channel.socket._make_ref()
        self.channel.messages_waiting_for_ack[self.ref] = self
        self.start_timeout()
        self.sent = True

        message = Message(
            topic=self.channel.topic,
            event=self.event,
            ref=self.ref,
            payload=self.payload,
        )
        await self.channel.socket.send(message)

    def update_payload(self, payload: Dict[str, Any]):
        self.payload = {**self.payload, **payload}

    @overload
    def receive(
        self,
        status: Literal[RealtimeAcknowledgementStatus.Ok],
        callback: Callback[[ReplyPostgresChanges], None],
    ) -> AsyncPush: ...
    @overload
    def receive(
        self,
        status: Literal[RealtimeAcknowledgementStatus.Error],
        callback: Callback[[Dict[str, Any]], None],
    ) -> AsyncPush: ...

    @overload
    def receive(
        self,
        status: Literal[RealtimeAcknowledgementStatus.Timeout],
        callback: Callback[[], None],
    ) -> AsyncPush: ...

    def receive(self, status, callback) -> AsyncPush:
        if (received := self.received_resp) and received[0] == status:
            callback(received[1])
        else:
            if status == RealtimeAcknowledgementStatus.Ok:
                self.ok_callbacks.append(callback)
            elif status == RealtimeAcknowledgementStatus.Error:
                self.error_callbacks.append(callback)
            elif status == RealtimeAcknowledgementStatus.Timeout:
                self.timeout_callbacks.append(callback)
            else:
                assert_never(status)
        return self

    def start_timeout(self):
        if self.timeout_task:
            return

        async def timeout(self):
            await asyncio.sleep(self.timeout)
            self.trigger(RealtimeAcknowledgementStatus.Timeout, {})
            if self.ref and self.ref in self.channel.messages_waiting_for_ack:
                del self.channel.messages_waiting_for_ack[self.ref]

        self.timeout_task = asyncio.create_task(timeout(self))

    @overload
    def trigger(
        self,
        status: Literal[RealtimeAcknowledgementStatus.Ok],
        response: ReplyPostgresChanges,
    ): ...
    @overload
    def trigger(
        self,
        status: Literal[RealtimeAcknowledgementStatus.Error],
        response: Dict[str, Any],
    ): ...
    @overload
    def trigger(
        self,
        status: Literal[RealtimeAcknowledgementStatus.Timeout],
        response: Dict[str, Any],
    ): ...

    def trigger(self, status: RealtimeAcknowledgementStatus, response) -> None:
        self.received_resp = (status, response)
        if status == RealtimeAcknowledgementStatus.Ok:
            for ok_callback in self.ok_callbacks:
                ok_callback(response)
        elif status == RealtimeAcknowledgementStatus.Error:
            for error_callback in self.error_callbacks:
                error_callback(response)
        elif status == RealtimeAcknowledgementStatus.Timeout:
            for timeout_callback in self.timeout_callbacks:
                timeout_callback()
        else:
            assert_never(status)

    def destroy(self):
        self._cancel_timeout()

    def _cancel_timeout(self):
        if not self.timeout_task:
            return

        self.timeout_task.cancel()
        self.timeout_task = None
