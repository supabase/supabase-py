import asyncio
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class AsyncTimer:
    def __init__(self, callback: Callable, timer_calc: Callable[[int], int]):
        self.callback = callback
        self.timer_calc = timer_calc
        self.timer: Optional[asyncio.Task] = None
        self.tries: int = 0

    def reset(self):
        self.tries = 0
        if self.timer and not self.timer.done():
            self.timer.cancel()
            self.timer = None
            logger.debug(
                "AsyncTimer has been reset and any scheduler tasks have been cancelled"
            )

    def schedule_timeout(self):
        if self.timer:
            self.timer.cancel()

        self.tries += 1
        delay = self.timer_calc(self.tries + 1)
        logger.debug(f"Scheduling callback to run after {delay} seconds.")
        self.timer = asyncio.create_task(self._run_timer(delay))

    async def _run_timer(self, delay: float):
        try:
            await asyncio.sleep(delay)
            await self.callback()
        except asyncio.CancelledError:
            logger.debug("AsyncTimer task was cancelled.")
        except Exception as e:
            logger.exception(f"Error in AsyncTimer callback: {e}")
