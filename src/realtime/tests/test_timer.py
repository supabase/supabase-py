import asyncio
from typing import NoReturn

import pytest

from realtime._async.timer import AsyncTimer


def linear_backoff(tries: int) -> float:
    return tries * 0.1


@pytest.mark.asyncio
async def test_timer_initialization() -> None:
    async def callback() -> None:
        pass

    timer = AsyncTimer(callback, linear_backoff)
    assert timer.tries == 0
    assert timer.timer is None
    assert timer.callback == callback
    assert timer.timer_calc == linear_backoff


@pytest.mark.asyncio
async def test_timer_schedule() -> None:
    callback_called = False

    async def callback() -> None:
        nonlocal callback_called
        callback_called = True

    timer = AsyncTimer(callback, linear_backoff)
    timer.schedule_timeout()

    assert timer.tries == 1
    assert timer.timer is not None
    assert not timer.timer.done()

    # Wait for the timer to complete
    await timer.timer
    assert callback_called


@pytest.mark.asyncio
async def test_timer_reset() -> None:
    callback_called = False

    async def callback() -> None:
        nonlocal callback_called
        callback_called = True

    timer = AsyncTimer(callback, linear_backoff)
    timer.schedule_timeout()

    # Reset before the timer completes
    timer.reset()
    assert timer.tries == 0
    assert timer.timer is None

    # Wait a bit to ensure the original timer doesn't fire
    await asyncio.sleep(0.2)
    assert not callback_called


@pytest.mark.asyncio
async def test_timer_multiple_schedules() -> None:
    callback_count = 0

    async def callback() -> None:
        nonlocal callback_count
        callback_count += 1

    timer = AsyncTimer(callback, linear_backoff)

    # Schedule multiple times
    timer.schedule_timeout()
    timer.schedule_timeout()
    timer.schedule_timeout()

    assert timer.tries == 3
    assert timer.timer is not None

    # Wait for the last timer to complete
    await timer.timer
    assert callback_count == 1  # Only the last schedule should fire


@pytest.mark.asyncio
async def test_timer_callback_error() -> None:
    async def callback() -> NoReturn:
        raise ValueError("Test error")

    timer = AsyncTimer(callback, linear_backoff)
    timer.schedule_timeout()
    assert timer.timer is not None

    # Wait for the timer to complete
    await timer.timer
    # The error should be caught and logged, but not re-raised
    assert timer.timer.done()


@pytest.mark.asyncio
async def test_timer_cancellation() -> None:
    callback_called = False

    async def callback() -> None:
        nonlocal callback_called
        callback_called = True

    timer = AsyncTimer(callback, linear_backoff)
    timer.schedule_timeout()

    # Cancel the timer
    assert timer.timer is not None
    timer.timer.cancel()

    # Wait a bit to ensure the timer doesn't fire
    await asyncio.sleep(0.2)
    assert not callback_called
    assert timer.timer.done()
    assert timer.timer.cancelled()
