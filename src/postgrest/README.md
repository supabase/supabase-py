# postgrest-py

[PostgREST](https://postgrest.org) client for Python. This library provides an "ORM-like" interface to PostgREST.

## INSTALLATION

### Requirements

- Python >= 3.9
- PostgreSQL >= 13
- PostgREST >= 11

### Local PostgREST server

If you want to use a local PostgREST server for development, you can use our preconfigured instance via Docker Compose.

```sh
docker-compose up
```

Once Docker Compose started, PostgREST is accessible at <http://localhost:3000>.

### Instructions

#### With uv (recommended)

```sh
uv add postgrest
```

#### With Pip

```sh
pip install postgrest
```

## USAGE

### Getting started

```py
import asyncio
from postgrest import AsyncPostgrestClient

async def main():
    async with AsyncPostgrestClient("http://localhost:3000") as client:
        r = await client.from_("countries").select("*").execute()
        countries = r.data

asyncio.run(main())
```

### Create

```py
await client.from_("countries").insert({ "name": "Việt Nam", "capital": "Hà Nội" }).execute()
```

### Read

```py
r = await client.from_("countries").select("id", "name").execute()
countries = r.data
```

### Update

```py
await client.from_("countries").update({"capital": "Hà Nội"}).eq("name", "Việt Nam").execute()
```

### Delete

```py
await client.from_("countries").delete().eq("name", "Việt Nam").execute()
```

### General filters

### Stored procedures (RPC)
```py
await client.rpc("foobar", {"arg1": "value1", "arg2": "value2"}).execute()
```

## CHANGELOG

Read more [here](https://github.com/supabase/postgrest-py/blob/main/CHANGELOG.md).

## SPONSORS

We are building the features of Firebase using enterprise-grade, open source products. We support existing communities wherever possible, and if the products don’t exist we build them and open source them ourselves. Thanks to these sponsors who are making the OSS ecosystem better for everyone.

[![Worklife VC](https://user-images.githubusercontent.com/10214025/90451355-34d71200-e11e-11ea-81f9-1592fd1e9146.png)](https://www.worklife.vc)
[![New Sponsor](https://user-images.githubusercontent.com/10214025/90518111-e74bbb00-e198-11ea-8f88-c9e3c1aa4b5b.png)](https://github.com/sponsors/supabase)
