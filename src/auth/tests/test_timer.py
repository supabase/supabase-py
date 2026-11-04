import asyncio
import threading
import time

from supabase_auth.timer import _AsyncTimer, _SyncTimer


async def test_async_timer_waits_given_milliseconds() -> None:
    called = asyncio.Event()

    async def callback() -> None:
        called.set()

    timer = _AsyncTimer(milliseconds=50, function=callback)
    start = time.monotonic()
    timer.start()
    await asyncio.wait_for(called.wait(), timeout=1)
    elapsed = time.monotonic() - start

    assert 0.04 <= elapsed < 0.5


async def test_async_timer_cancel_prevents_call() -> None:
    called = asyncio.Event()

    async def callback() -> None:
        called.set()

    timer = _AsyncTimer(milliseconds=50, function=callback)
    timer.start()
    assert timer.is_alive()
    timer.cancel()
    await asyncio.sleep(0.2)

    assert not called.is_set()
    assert not timer.is_alive()


def test_sync_timer_waits_given_milliseconds() -> None:
    called = threading.Event()

    timer = _SyncTimer(milliseconds=50, function=called.set)
    start = time.monotonic()
    timer.start()
    assert called.wait(timeout=1)
    elapsed = time.monotonic() - start

    assert 0.04 <= elapsed < 0.5


def test_sync_timer_cancel_prevents_call() -> None:
    called = threading.Event()

    timer = _SyncTimer(milliseconds=50, function=called.set)
    timer.start()
    assert timer.is_alive()
    timer.cancel()

    assert not called.wait(timeout=0.2)
    assert not timer.is_alive()
