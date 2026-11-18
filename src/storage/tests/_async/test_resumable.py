from __future__ import annotations

import shelve
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

from storage3 import (
    DEFAULT_CHUNK_SIZE,
    ResumableUploadCancelledError,
    ResumableUploadPausedError,
    StorageApiError,
)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
    from pathlib import Path

    from supabase_utils.http.io import AsyncHttpIO

    from storage3 import AsyncStorageClient, StorageFileApiClient

DATA = bytes(index % 251 for index in range(DEFAULT_CHUNK_SIZE * 2 + 1000))


@pytest.fixture
async def bucket(
    storage: AsyncStorageClient,
) -> AsyncGenerator[StorageFileApiClient[AsyncHttpIO]]:
    bucket_id = f"resumable-{uuid4().hex[:8]}"
    await storage.create_bucket(id=bucket_id)
    yield storage.from_(bucket_id)
    await storage.empty_bucket(bucket_id)
    await storage.delete_bucket(bucket_id)


async def test_uploads_a_file_larger_than_one_chunk(
    bucket: StorageFileApiClient[AsyncHttpIO], tmp_path: Path
) -> None:
    path = tmp_path / "large.bin"
    path.write_bytes(DATA)
    reports: list[int] = []

    def record(moved: int, total: int | None) -> None:
        assert total == len(DATA)
        reports.append(moved)

    response = await bucket.resumable_upload(
        "folder/large.bin",
        path,
        content_type="application/octet-stream",
        metadata={"source": "test"},
        on_progress=record,
    ).run()

    assert response.full_path == f"{bucket.id}/folder/large.bin"
    assert response.id is not None
    assert await bucket.download("folder/large.bin") == DATA
    info = await bucket.info("folder/large.bin")
    assert info.metadata == {"source": "test"}
    assert reports[-1] == len(DATA)


async def test_uploads_an_empty_file(
    bucket: StorageFileApiClient[AsyncHttpIO],
) -> None:
    await bucket.resumable_upload("empty.txt", b"").run()

    assert await bucket.download("empty.txt") == b""


async def test_continues_a_paused_upload_after_a_restart(
    bucket: StorageFileApiClient[AsyncHttpIO], tmp_path: Path
) -> None:
    def pause_after_the_first_chunk(moved: int, total: int | None) -> None:
        if moved >= DEFAULT_CHUNK_SIZE:
            first.pause()

    with shelve.open(str(tmp_path / "uploads")) as store:
        first = bucket.resumable_upload(
            "restart.bin", DATA, store=store, on_progress=pause_after_the_first_chunk
        )
        with pytest.raises(ResumableUploadPausedError):
            await first.run()
        assert first.offset == DEFAULT_CHUNK_SIZE

    with shelve.open(str(tmp_path / "uploads")) as store:
        second = bucket.resumable_upload("restart.bin", DATA, store=store)
        await second.run()
        assert dict(store) == {}

    assert await bucket.download("restart.bin") == DATA


async def test_refuses_to_overwrite_an_object_without_upsert(
    bucket: StorageFileApiClient[AsyncHttpIO],
) -> None:
    await bucket.upload("existing.txt", b"1")

    with pytest.raises(StorageApiError) as caught:
        await bucket.resumable_upload("existing.txt", b"2").run()

    assert caught.value.status_code == 409
    assert caught.value.code == "Duplicate"


async def test_overwrites_an_object_with_upsert(
    bucket: StorageFileApiClient[AsyncHttpIO],
) -> None:
    await bucket.upload("existing.txt", b"1")

    await bucket.resumable_upload("existing.txt", b"2", upsert=True).run()

    assert await bucket.download("existing.txt") == b"2"


async def test_cancels_an_upload(
    bucket: StorageFileApiClient[AsyncHttpIO],
) -> None:
    def pause(moved: int, total: int | None) -> None:
        if moved > 0:
            upload.pause()

    upload = bucket.resumable_upload("cancelled.bin", DATA, on_progress=pause)
    with pytest.raises(ResumableUploadPausedError):
        await upload.run()
    url = upload.url
    assert url is not None

    await upload.cancel()

    with pytest.raises(ResumableUploadCancelledError):
        await upload.run()
    assert not await bucket.exists("cancelled.bin")
