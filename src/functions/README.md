# Functions-py

## Installation
The package can be installed using pip, uv or poetry:
### Pip
```bash
pip install supabase_functions
```
### UV
```bash
uv add supabase_functions
```
### Poetry
```bash
poetry add supabase_functions
```

## Usage

Deploy your Edge Function following the [Supabase Functions documentation](https://supabase.com/docs/guides/functions).


### Asynchronous Client

```python
import asyncio
from supabase_functions import AsyncFunctionsClient

async def run_func():
    # Initialize the client with your project URL and optional headers
    headers = {
        "Authorization": "Bearer your-publishable-key",
        # Add any other headers you might need
    }
    
    fc = AsyncFunctionsClient("https://<project_ref>.functions.supabase.co", headers)
    
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
from supabase_functions import SyncFunctionsClient

# Initialize the client
headers = {"Authorization": "Bearer your-publishable-key"}
fc = SyncFunctionsClient("https://<project_ref>.functions.supabase.co", headers)

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

### Advanced Usage: Custom Headers & Payload

For production scenarios, you can pass custom headers and structured payloads:

```python
from supabase_functions import SyncFunctionsClient

# Initialize with custom headers
headers = {
    "Authorization": "Bearer your-anon-key",
    "X-Client-Info": "my-app-v1"
}
client = SyncFunctionsClient("https://<project_ref>.functions.supabase.co", headers)

try:
    # Invoke with structured body
    response = client.invoke("hello-world", {
        "body": {"name": "Supabase"},
        "responseType": "json"
    })
    print("Success:", response)
except Exception as e:
    print(f"Error: {e}")
```
