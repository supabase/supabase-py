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
