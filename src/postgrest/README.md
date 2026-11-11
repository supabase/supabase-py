# postgrest-py

[PostgREST](https://postgrest.org) client for Python. This library provides an "ORM-like" interface to PostgREST.

## INSTALLATION

### Requirements

- Python >= 3.12
- PostgreSQL >= 13
- PostgREST >= 11

### Local PostgREST server

If you want to use a local PostgREST server for development, you can use our preconfigured instance via Docker Compose.

```sh
docker compose -f infra/docker-compose.yaml up
```

Once Docker Compose started, PostgREST is accessible at <http://localhost:3000>.

### Instructions

The package needs an HTTP client adapter. The examples below use httpx:

#### With uv (recommended)

```sh
uv add postgrest "supabase_utils[httpx]"
```

#### With Pip

```sh
pip install postgrest "supabase_utils[httpx]"
```

## Supabase Service Compatibility

`postgrest` only guarantees compatibility with the [latest PostgREST release](https://github.com/PostgREST/postgrest/releases). Older PostgREST releases are supported on a best-effort basis, but compatibility is not guaranteed.

If you self-host PostgREST, we recommend upgrading to the latest release when upgrading this SDK.

## USAGE

### Getting started

The client takes the URL of the PostgREST service and the HTTP session it sends its requests with. Leaving the client's context manager closes the session:

```py
import asyncio

from httpx import AsyncClient
from postgrest import AsyncPostgrestClient
from supabase_utils.http.adapters.httpx import AsyncHttpxSession


async def main() -> None:
    async with AsyncPostgrestClient(
        "http://localhost:3000", AsyncHttpxSession(AsyncClient())
    ) as client:
        r = await client.from_("countries").select("*").execute()
        countries = r.data


asyncio.run(main())
```

`SyncPostgrestClient` with an `HttpxSession` works the same way without `await`. The examples below use the async `client` from above.

### Create

```py
await client.from_("countries").insert({ "name": "Việt Nam", "capital": "Hà Nội" }).execute()
```

### Read

```py
r = await client.from_("countries").select("id", "name").execute()
countries = r.data
```

### Reuse a query

Every builder method returns a new query and leaves the original unchanged, so one base query can branch into several requests. Each request sends only its own filters.

```py
asian_countries = client.from_("countries").select("id", "name").eq("continent", "Asia")
large = await asian_countries.gte("population", 100_000_000).execute()
small = await asian_countries.lt("population", 1_000_000).execute()
```

### Update

```py
await client.from_("countries").update({"capital": "Hà Nội"}).eq("name", "Việt Nam").execute()
```

An update or a delete without a filter would affect every row in the table, so executing one raises `ValueError` before anything is sent. To affect every row on purpose, call `all()`:

```py
await client.from_("countries").update({"visited": False}).all().execute()
```

### Delete

```py
await client.from_("countries").delete().eq("name", "Việt Nam").execute()
await client.from_("countries").delete().all().execute()
```

### Stored procedures (RPC)
```py
await client.rpc("foobar", {"arg1": "value1", "arg2": "value2"}).execute()
```

## CHANGELOG

Read more [here](https://github.com/supabase/supabase-py/blob/main/src/postgrest/CHANGELOG.md).
