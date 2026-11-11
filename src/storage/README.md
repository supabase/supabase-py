# Storage-py

Python Client library to interact with Supabase Storage.

## Supabase Service Compatibility

`storage3` only guarantees compatibility with the [latest Supabase Storage release](https://github.com/supabase/storage/releases). Older Supabase Storage releases are supported on a best-effort basis, but compatibility is not guaranteed.

If you self-host Supabase Storage, we recommend upgrading to the latest release when upgrading this SDK.

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
