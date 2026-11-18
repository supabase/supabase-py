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
    from collections.abc import Generator
    from pathlib import Path

    from supabase_utils.http.io import SyncHttpIO

    from storage3 import StorageFileApiClient, SyncStorageClient

DATA = bytes(index % 251 for index in range(DEFAULT_CHUNK_SIZE * 2 + 1000))


@pytest.fixture
def bucket(
    storage: SyncStorageClient,
) -> Generator[StorageFileApiClient[SyncHttpIO]]:
    bucket_id = f"resumable-{uuid4().hex[:8]}"
    storage.create_bucket(id=bucket_id)
    yield storage.from_(bucket_id)
    storage.empty_bucket(bucket_id)
    storage.delete_bucket(bucket_id)


def test_uploads_a_file_larger_than_one_chunk(
    bucket: StorageFileApiClient[SyncHttpIO], tmp_path: Path
) -> None:
    path = tmp_path / "large.bin"
    path.write_bytes(DATA)
    reports: list[int] = []

    def record(moved: int, total: int | None) -> None:
        assert total == len(DATA)
        reports.append(moved)

    response = bucket.resumable_upload(
        "folder/large.bin",
        path,
        content_type="application/octet-stream",
        metadata={"source": "test"},
        on_progress=record,
    ).run()

    assert response.full_path == f"{bucket.id}/folder/large.bin"
    assert response.id is not None
    assert bucket.download("folder/large.bin") == DATA
    info = bucket.info("folder/large.bin")
    assert info.metadata == {"source": "test"}
    assert reports[-1] == len(DATA)


def test_uploads_an_empty_file(
    bucket: StorageFileApiClient[SyncHttpIO],
) -> None:
    bucket.resumable_upload("empty.txt", b"").run()

    assert bucket.download("empty.txt") == b""


def test_continues_a_paused_upload_after_a_restart(
    bucket: StorageFileApiClient[SyncHttpIO], tmp_path: Path
) -> None:
    def pause_after_the_first_chunk(moved: int, total: int | None) -> None:
        if moved >= DEFAULT_CHUNK_SIZE:
            first.pause()

    with shelve.open(str(tmp_path / "uploads")) as store:
        first = bucket.resumable_upload(
            "restart.bin", DATA, store=store, on_progress=pause_after_the_first_chunk
        )
        with pytest.raises(ResumableUploadPausedError):
            first.run()
        assert first.offset == DEFAULT_CHUNK_SIZE

    with shelve.open(str(tmp_path / "uploads")) as store:
        second = bucket.resumable_upload("restart.bin", DATA, store=store)
        second.run()
        assert dict(store) == {}

    assert bucket.download("restart.bin") == DATA


def test_refuses_to_overwrite_an_object_without_upsert(
    bucket: StorageFileApiClient[SyncHttpIO],
) -> None:
    bucket.upload("existing.txt", b"1")

    with pytest.raises(StorageApiError) as caught:
        bucket.resumable_upload("existing.txt", b"2").run()

    assert caught.value.status_code == 409
    assert caught.value.code == "Duplicate"


def test_overwrites_an_object_with_upsert(
    bucket: StorageFileApiClient[SyncHttpIO],
) -> None:
    bucket.upload("existing.txt", b"1")

    bucket.resumable_upload("existing.txt", b"2", upsert=True).run()

    assert bucket.download("existing.txt") == b"2"


def test_cancels_an_upload(
    bucket: StorageFileApiClient[SyncHttpIO],
) -> None:
    def pause(moved: int, total: int | None) -> None:
        if moved > 0:
            upload.pause()

    upload = bucket.resumable_upload("cancelled.bin", DATA, on_progress=pause)
    with pytest.raises(ResumableUploadPausedError):
        upload.run()
    url = upload.url
    assert url is not None

    upload.cancel()

    with pytest.raises(ResumableUploadCancelledError):
        upload.run()
    assert not bucket.exists("cancelled.bin")
