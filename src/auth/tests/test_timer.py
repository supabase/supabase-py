import asyncio
import threading
import time

from supabase_auth.timer import _AsyncTimer, _SyncTimer


async def test_async_timer_waits_given_seconds() -> None:
    called = asyncio.Event()

    async def callback() -> None:
        called.set()

    timer = _AsyncTimer(seconds=0.05, function=callback)
    start = time.monotonic()
    timer.start()
    await asyncio.wait_for(called.wait(), timeout=1)
    elapsed = time.monotonic() - start

    assert 0.04 <= elapsed < 0.5


async def test_async_timer_cancel_prevents_call() -> None:
    called = asyncio.Event()

    async def callback() -> None:
        called.set()

    timer = _AsyncTimer(seconds=0.05, function=callback)
    timer.start()
    assert timer.is_alive()
    timer.cancel()
    await asyncio.sleep(0.2)

    assert not called.is_set()
    assert not timer.is_alive()


def test_sync_timer_waits_given_seconds() -> None:
    called = threading.Event()

    timer = _SyncTimer(seconds=0.05, function=called.set)
    start = time.monotonic()
    timer.start()
    assert called.wait(timeout=1)
    elapsed = time.monotonic() - start

    assert 0.04 <= elapsed < 0.5


def test_sync_timer_cancel_prevents_call() -> None:
    called = threading.Event()

    timer = _SyncTimer(seconds=0.3, function=called.set)
    timer.start()
    assert timer.is_alive()
    timer.cancel()

    assert not called.wait(timeout=0.5)
    assert not timer.is_alive()


async def test_async_timer_cancel_from_its_own_callback_lets_it_finish() -> None:
    finished = asyncio.Event()
    timer: _AsyncTimer

    async def callback() -> None:
        timer.cancel()
        await asyncio.sleep(0)
        finished.set()

    timer = _AsyncTimer(seconds=0, function=callback)
    timer.start()
    await asyncio.wait_for(finished.wait(), timeout=1)

    assert not timer.is_alive()


async def test_async_timer_cancel_from_another_task_stops_the_callback() -> None:
    started = asyncio.Event()
    finished = False

    async def callback() -> None:
        nonlocal finished
        started.set()
        await asyncio.sleep(10)
        finished = True

    timer = _AsyncTimer(seconds=0, function=callback)
    timer.start()
    await asyncio.wait_for(started.wait(), timeout=1)
    timer.cancel()
    await asyncio.sleep(0)

    assert not finished
    assert not timer.is_alive()
