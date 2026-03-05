import asyncio
from threading import Timer
from typing import Awaitable, Callable


class AsyncTimer:
    def __init__(
        self,
        seconds: float,
        function: Callable[[], Awaitable[None]],
    ) -> None:
        self._milliseconds = seconds
        self._function = function
        self._task: asyncio.Task[None] | None = None

    def start(self) -> None:
        async def schedule() -> None:
            await asyncio.sleep(self._milliseconds / 1000)
            await self._function()

        def cleanup(_task: asyncio.Task[None]) -> None:
            self._task = None

        self._task = asyncio.create_task(schedule())
        self._task.add_done_callback(cleanup)

    def cancel(self) -> None:
        if self._task is not None:
            self._task.cancel()
            self._task = None

    def is_alive(self) -> bool:
        return self._task is not None


class SyncTimer:
    def __init__(
        self,
        seconds: float,
        function: Callable[[], None],
    ) -> None:
        self._milliseconds = seconds
        self._function = function
        self._timer: Timer | None = None

    def start(self) -> None:
        self._timer = Timer(self._milliseconds / 1000, self._function)
        self._timer.daemon = True
        self._timer.start()

    def cancel(self) -> None:
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

    def is_alive(self) -> bool:
        return self._timer is not None and self._timer.is_alive()
