import asyncio
from typing import Any, Callable, Coroutine


class AsyncFinalizerFactory:
    def __init__(self, finalizer: Callable[[], Coroutine[Any, Any, None]]):
        def func():
            event_loop = asyncio.get_event_loop_policy().get_event_loop()
            return event_loop.run_until_complete(finalizer())

        self.finalizer = func


class SyncFinalizerFactory:
    def __init__(self, finalizer: Callable[[], None]):
        self.finalizer = finalizer
