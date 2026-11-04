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


### Asynchronous Client

```python
import asyncio

from httpx import AsyncClient
from supabase_functions import AsyncFunctionsClient
from supabase_utils.http.adapters.httpx import AsyncHttpxSession

async def run_func():
    # Initialize the client with your project URL and optional headers
    headers = {
        "Authorization": "Bearer your-publishable-key",
        # Add any other headers you might need
    }
    
    fc = AsyncFunctionsClient(
        "https://<project_ref>.functions.supabase.co",
        headers,
        http_session=AsyncHttpxSession(client=AsyncClient()),
    )
    
    try:
        # Invoke your Edge Function
        res = await fc.invoke("payment-sheet", {
            "responseType": "json",
            "body": {"amount": 1000, "currency": "usd"}
        })
        print("Response:", res)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(run_func())
```
### Synchronous Client
```python
from httpx import Client
from supabase_functions import SyncFunctionsClient
from supabase_utils.http.adapters.httpx import HttpxSession

# Initialize the client
headers = {"Authorization": "Bearer your-publishable-key"}
fc = SyncFunctionsClient(
    "https://<project_ref>.functions.supabase.co",
    headers,
    http_session=HttpxSession(client=Client()),
)

# Invoke your Edge Function
try:
    res = fc.invoke("payment-sheet", {
        "responseType": "json", 
        "body": {"amount": 1000, "currency": "usd"}
    })
    print("Response:", res)
except Exception as e:
    print(f"Error: {e}")
```
