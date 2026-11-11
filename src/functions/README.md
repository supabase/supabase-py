# Functions-py

## Installation
The package can be installed using pip, uv or poetry. It needs an HTTP client adapter, the examples below use httpx:
### Pip
```bash
pip install supabase_functions "supabase_utils[httpx]"
```
### UV
```bash
uv add supabase_functions "supabase_utils[httpx]"
```
### Poetry
```bash
poetry add supabase_functions "supabase_utils[httpx]"
```

## Supabase Service Compatibility

`supabase_functions` only guarantees compatibility with the [latest Supabase Edge Runtime release](https://github.com/supabase/edge-runtime/releases). Older Supabase Edge Runtime releases are supported on a best-effort basis, but compatibility is not guaranteed.

If you self-host the Supabase Edge Runtime, we recommend upgrading to the latest release when upgrading this SDK.

## Usage

Deploy your Edge Function following the [Supabase Functions documentation](https://supabase.com/docs/guides/functions).


The client takes the URL of your functions, the headers to send, and the HTTP session it sends its requests with. Leaving the session's context manager closes it. A function that answers with an error status raises `FunctionsHttpError`, and one the relay could not reach raises `FunctionsRelayError`.

### Asynchronous Client

```python
import asyncio

from httpx import AsyncClient
from supabase_functions import (
    AsyncFunctionsClient,
    FunctionsHttpError,
    FunctionsRelayError,
)
from supabase_utils.http.adapters.httpx import AsyncHttpxSession


async def run_func() -> None:
    headers = {"apikey": "your-publishable-key"}

    async with AsyncHttpxSession(AsyncClient(follow_redirects=True)) as session:
        functions = AsyncFunctionsClient(
            "https://<project_ref>.supabase.co/functions/v1",
            headers,
            session,
        )

        try:
            response = await functions.invoke(
                "payment-sheet", body={"amount": 1000, "currency": "usd"}
            )
            print("Response:", response.content)
        except (FunctionsHttpError, FunctionsRelayError) as error:
            print(error.status_code, error.message)


if __name__ == "__main__":
    asyncio.run(run_func())
```

### Synchronous Client

```python
from httpx import Client
from supabase_functions import FunctionsHttpError, FunctionsRelayError, SyncFunctionsClient
from supabase_utils.http.adapters.httpx import HttpxSession

headers = {"apikey": "your-publishable-key"}

with HttpxSession(Client(follow_redirects=True)) as session:
    functions = SyncFunctionsClient(
        "https://<project_ref>.supabase.co/functions/v1",
        headers,
        session,
    )

    try:
        response = functions.invoke(
            "payment-sheet", body={"amount": 1000, "currency": "usd"}
        )
        print("Response:", response.content)
    except (FunctionsHttpError, FunctionsRelayError) as error:
        print(error.status_code, error.message)
```
