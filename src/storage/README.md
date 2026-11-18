# Storage-py

Python Client library to interact with Supabase Storage.

## Supabase Service Compatibility

`storage3` only guarantees compatibility with the [latest Supabase Storage release](https://github.com/supabase/storage/releases). Older Supabase Storage releases are supported on a best-effort basis, but compatibility is not guaranteed.

If you self-host Supabase Storage, we recommend upgrading to the latest release when upgrading this SDK. Listing objects with `list()` needs Supabase Storage v1.19.0 or newer, which added `POST /object/list-v2`. The `limit`, `offset`, `search`, `sort_column` and `sort_order` arguments of `list_buckets()` need v1.25.0 or newer; older releases ignore them and return every bucket.

## Installation

The package needs an HTTP client adapter. The examples below use httpx:

```bash
pip install storage3 "supabase_utils[httpx]"
# or
uv add storage3 "supabase_utils[httpx]"
```

## How to use

Most users use storage through the main [Supabase Python client](https://github.com/supabase/supabase-py/blob/main/src/supabase/README.md), as `client.storage`, which sets the headers for you.

The client takes the URL of the storage service, the headers to send, and the HTTP session it sends its requests with. Leaving the client's context manager closes the session:

```python
import asyncio

from httpx import AsyncClient
from storage3 import AsyncStorageClient
from supabase_utils.http.adapters.httpx import AsyncHttpxSession

url = "https://<project_ref>.supabase.co/storage/v1/"
key = "<your api key>"
headers = {"apikey": key, "Authorization": f"Bearer {key}"}


async def main() -> None:
    async with AsyncStorageClient(
        url, headers, AsyncHttpxSession(AsyncClient())
    ) as storage_client:
        buckets = await storage_client.list_buckets()
        print(buckets)


asyncio.run(main())
```

`SyncStorageClient` with an `HttpxSession` works the same way without `await`.

### Uploading files

When uploading files, set the MIME type with the `content_type` argument:

```python
from pathlib import Path

await storage_client.from_("bucket").upload(
    "folder/file.png", Path("file.png"), content_type="image/png"
)
```

If no MIME type is given, `text/plain;charset=UTF-8` is used.

A path or an open binary file is streamed from disk, and an iterator over bytes (an async iterator on the async client) is streamed as it is read, so a large file is never held in memory.

### Resumable uploads

`resumable_upload` sends a large file in 6 MiB chunks with the [tus protocol](https://tus.io), so a failed upload continues from the last chunk the server holds instead of starting over:

```python
import shelve

from storage3 import ResumableUploadPausedError

with shelve.open("uploads") as store:
    upload = storage_client.from_("bucket").resumable_upload(
        "videos/intro.mp4", "intro.mp4", content_type="video/mp4", store=store
    )
    try:
        response = await upload.run()
    except ResumableUploadPausedError:
        print(f"Paused after {upload.offset} of {upload.size} bytes")
```

`upload.pause()` stops `run` after the chunk in flight, and calling `run` again continues the upload. `await upload.cancel()` deletes it on the server. A failed request is retried with the `RetryPolicy` of the client. The `store` keeps the URL of the upload, so a later `resumable_upload` of the same file to the same path continues it, even after a restart.

### Streaming downloads

`download_stream` gives the status and headers once the response head arrives, and the body as it arrives. Write it to a file, which is replaced only once the whole body arrived, or iterate over it chunk by chunk:

```python
async with storage_client.from_("bucket").download_stream("videos/intro.mp4") as download:
    print(download.status, download.content_length)
    await download.write_to("intro.mp4")
```

`read(max_bytes=...)` reads the body into memory and raises `StorageDownloadTooLargeError` once it grows past the cap.

### Transfer progress

`upload`, `update`, `upload_to_signed_url`, `download` and `download_stream` take an `on_progress` callback. It is called with the bytes moved so far and the total, which is `None` when it is not known, as for an iterator or a transformed image:

```python
from pathlib import Path


def on_progress(moved: int, total: int | None) -> None:
    print(f"{moved} of {total or '?'} bytes")

await storage_client.from_("bucket").upload(
    "videos/intro.mp4", Path("intro.mp4"), on_progress=on_progress
)
```

The count restarts from 0 when an upload or a `download` is retried. The callback can run in a worker thread.

### Byte ranges

`download` and `download_stream` take an `offset` and a `length` to download part of a file. The server answers a range with status 206 and a `Content-Range` header:

```python
first_bytes = await storage_client.from_("bucket").download(
    "videos/intro.mp4", length=512
)
```

A server or cache that ignores the range answers with status 200 and the whole file. `download` then raises `StorageRangeIgnoredError`, while `download_stream` returns the response as it is.

To resume a partial download, pass the size of the partial file as `offset` and `resume=True` to `write_to`. It appends a 206 body to the file and replaces the file with a 200 body. Keep the `etag` of the first download and pass it as `if_match`: when the file changed since, the server answers with HTTP 412 and `StorageApiError` with the code `PreconditionFailed` is raised before anything is written, so the partial file never mixes two versions. An `offset` at or past the end of the file, as for a file that is already complete, raises `StorageApiError` with the code `InvalidRange`:

```python
from pathlib import Path

partial = Path("intro.mp4")
etag_file = Path("intro.mp4.etag")
resuming = partial.exists() and etag_file.exists()
async with storage_client.from_("bucket").download_stream(
    "videos/intro.mp4",
    offset=partial.stat().st_size if resuming else 0,
    if_match=etag_file.read_text() if resuming else None,
) as download:
    if download.etag is not None:
        etag_file.write_text(download.etag)
    await download.write_to(partial, resume=True)
etag_file.unlink()
```

### File versions

A bucket created or updated with `versioning_status="ENABLED"` keeps the previous versions of a file when it is overwritten or removed. Removing a file then leaves a delete marker in its place. List the versions with `noncurrent_versions` and the delete markers with `delete_markers`, each `"include"` or `"only"`:

```python
await storage_client.create_bucket("documents", versioning_status="ENABLED")
documents = storage_client.from_("documents")

page = await documents.list("reports/", noncurrent_versions="include")
for entry in page.objects:
    print(entry.name, entry.version, entry.archived_at)
```

`download`, `download_stream`, `info`, `create_signed_url` and `get_public_url` take a `version_id`, and `copy` and `move` a `source_version_id`, to act on that version instead of the current one. Moving a version to its own path makes it the current version again. `remove` deletes exactly the version of a `FileVersion`:

```python
from storage3.types import FileVersion

documents = storage_client.from_("documents")
old = await documents.download("reports/q3.pdf", version_id="<version id>")
await documents.move("reports/q3.pdf", "reports/q3.pdf", source_version_id="<version id>")
await documents.remove([FileVersion("reports/q3.pdf", "<version id>")])
```

`update_bucket` with `versioning_status="SUSPENDED"` stops keeping new versions while the existing ones stay. A bucket cannot go back to `DISABLED`.
