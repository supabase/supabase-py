import asyncio
from threading import Timer as _Timer
from typing import Any, Callable, Coroutine, Optional, cast


class Timer:
    def __init__(
        self,
        seconds: float,
        function: Callable[[], Optional[Coroutine[Any, Any, None]]],
    ) -> None:
        self._milliseconds = seconds
        self._function = function
        self._task: Optional[asyncio.Task] = None
        self._timer: Optional[_Timer] = None

    def start(self) -> None:
        if asyncio.iscoroutinefunction(self._function):

            async def schedule():
                await asyncio.sleep(self._milliseconds / 1000)
                await cast(Coroutine[Any, Any, None], self._function())

            def cleanup(_):
                self._task = None

            self._task = asyncio.create_task(schedule())
            self._task.add_done_callback(cleanup)
        else:
            self._timer = _Timer(self._milliseconds / 1000, self._function)
            self._timer.daemon = True
            self._timer.start()

    def cancel(self) -> None:
        if self._task is not None:
            self._task.cancel()
            self._task = None
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

    def is_alive(self) -> bool:
        return self._task is not None or (
            self._timer is not None and self._timer.is_alive()
        )
