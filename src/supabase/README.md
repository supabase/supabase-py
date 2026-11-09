# `supabase-py`

Python client for [Supabase](https://supabase.com)

- Documentation: [supabase.com/docs](https://supabase.com/docs/reference/python/introduction)
- Usage:
  - [GitHub OAuth in your Python Flask app](https://supabase.com/blog/oauth2-login-python-flask-apps)
  - [Python data loading with Supabase](https://supabase.com/blog/loading-data-supabase-python)

### PyPI installation

Install the package (for Python >= 3.12) with the HTTP library the client should use. The `httpx` extra supports both the sync and the async client, and the `aiohttp` extra supports the async client:

```bash
# with pip
pip install "supabase[httpx]"

# with uv
uv add "supabase[httpx]"

# with conda
conda install -c conda-forge supabase httpx h2
```

Use `supabase[aiohttp]` instead to run the async client on aiohttp.

## Supabase Service Compatibility

`supabase` only guarantees compatibility with the latest release of each Supabase service, unless a minimum supported version is explicitly listed below.

Older service releases are supported on a best-effort basis, but compatibility is not guaranteed.

If you self-host Supabase, we recommend upgrading your services to their latest releases when upgrading the SDK.

| Service   | SDK package                                                         | Server releases                                                            | Lowest supported version |
| --------- | ------------------------------------------------------------------- | -------------------------------------------------------------------------- | ------------------------ |
| Auth      | [`supabase_auth`](https://pypi.org/project/supabase_auth)           | [supabase/auth](https://github.com/supabase/auth/releases)                 | Latest release           |
| Storage   | [`storage3`](https://pypi.org/project/storage3)                     | [supabase/storage](https://github.com/supabase/storage/releases)           | Latest release           |
| Functions | [`supabase_functions`](https://pypi.org/project/supabase_functions) | [supabase/edge-runtime](https://github.com/supabase/edge-runtime/releases) | Latest release           |
| PostgREST | [`postgrest`](https://pypi.org/project/postgrest)                   | [PostgREST/postgrest](https://github.com/PostgREST/postgrest/releases)     | Latest release           |
| Realtime  | [`realtime`](https://pypi.org/project/realtime)                     | [supabase/realtime](https://github.com/supabase/realtime/releases)         | Latest release           |

## Usage

Set your Supabase environment variables in a dotenv file, or using the shell:

```bash
export SUPABASE_URL="my-url-to-my-awesome-supabase-instance"
export SUPABASE_KEY="my-supa-dupa-secret-supabase-api-key"
```

Init client:

```python
import os
from supabase import Client
from supabase.httpx import create_client

url: str = os.environ["SUPABASE_URL"]
key: str = os.environ["SUPABASE_KEY"]
supabase: Client = create_client(url, key)
```

For the async client, use `create_async_client` from `supabase.httpx` or `supabase.aiohttp`, which returns an `AsyncClient`.

Settings are keyword arguments. `headers` and `request_timeout` apply to the database, auth, storage and edge functions, not to the realtime connection of `AsyncClient`. The settings of one service are grouped in an options class:

```python
from supabase import AuthClientOptions, PostgrestClientOptions, StorageClientOptions

supabase = create_client(
    url,
    key,
    headers={"x-app": "my-app"},
    request_timeout=30,
    postgrest=PostgrestClientOptions(schema="private"),
    auth=AuthClientOptions(flow_type="implicit"),
    storage=StorageClientOptions(request_timeout=120),
)
```

`request_timeout` is in seconds. The `request_timeout` of a service's options overrides the global one for that service.

Use the supabase client to interface with your database.

### Sign-up

```python
user = supabase.auth.sign_up({ "email": users_email, "password": users_password })
```

### Sign-in

```python
user = supabase.auth.sign_in_with_password({ "email": users_email, "password": users_password })
```

### Insert Data

```python
data = supabase.table("countries").insert({"name":"Germany"}).execute()

# Assert we pulled real data.
assert len(data.data) > 0
```

### Select Data

```python
data = supabase.table("countries").select("*").eq("country", "IL").execute()

# Assert we pulled real data.
assert len(data.data) > 0
```

### Update Data

```python
data = supabase.table("countries").update({"country": "Indonesia", "capital_city": "Jakarta"}).eq("id", 1).execute()
```

### Update data with duplicate keys

```python
country = {
  "country": "United Kingdom",
  "capital_city": "London" # This was missing when it was added
}

data = supabase.table("countries").upsert(country).execute()
assert len(data.data) > 0
```

### Delete Data

```python
data = supabase.table("countries").delete().eq("id", 1).execute()
```

### Call Edge Functions

```python
def test_func():
  try:
    resp = supabase.functions.invoke("hello-world", body={})
    return resp
  except (FunctionsRelayError, FunctionsHttpError) as exception:
    print(exception.status_code, exception.message)
```

### Download a file from Storage

```python
bucket_name: str = "photos"

data = supabase.storage.from_(bucket_name).download("photo1.png")
```

### Upload a file

```python
bucket_name: str = "photos"
new_file = getUserFile()

data = supabase.storage.from_(bucket_name).upload("/user1/profile.png", new_file)
```

### Remove a file

```python
bucket_name: str = "photos"

data = supabase.storage.from_(bucket_name).remove(["old_photo.png", "image5.jpg"])
```

### List all files

```python
bucket_name: str = "charts"

data = supabase.storage.from_(bucket_name).list()
```

### Move and rename files

```python
bucket_name: str = "charts"
old_file_path: str = "generic/graph1.png"
new_file_path: str = "important/revenue.png"

data = supabase.storage.from_(bucket_name).move(old_file_path, new_file_path)
```

## Error handling

Every exception the client raises inherits from `SupabaseError`, so one clause catches them all:

```python
from supabase import SupabaseAPIError, SupabaseError, SupabaseTransportError

try:
    data = supabase.table("countries").select("*").execute()
except SupabaseAPIError as error:
    # A service answered with an error.
    print(error.status_code, error.code, error.message)
except SupabaseTransportError as error:
    # No response could be read. The httpx or aiohttp exception is the cause.
    print(error.__cause__)
except SupabaseError as error:
    # The client failed on its own, such as a missing session.
    print(error.message)
```

Every error has a `message`, also returned by `str(error)`, and a `code` that is the identifier of the failure when the service or the client named it, such as `weak_password` or `PGRST116`. A `SupabaseAPIError` adds the `status_code` and the `response` of the failed request, whose headers carry the `sb-request-id` to quote when asking for support. A `SupabaseTransportError` adds the `request` that was sent. It is raised when the connection failed, the request timed out, or the HTTP client gave up, as on a redirect loop. The outcome of such a request is unknown, since it may have reached the service.

```
SupabaseError
├── SupabaseAPIError                A service answered with an error.
│   ├── AuthApiError                   ├── AuthRetryableError, AuthWeakPasswordError
│   ├── AuthUnknownError               The auth error body could not be parsed.
│   ├── PostgrestAPIError              message, code, hint and details of the PostgREST error.
│   ├── StorageApiError
│   ├── FunctionsHttpError
│   └── FunctionsRelayError
├── SupabaseTransportError          No response could be read. The HTTP client's exception is `__cause__`.
│   └── RequestTimeoutError            Also a built-in `TimeoutError`.
├── AuthError                       Root of the auth errors.
│   └── CustomAuthError                Raised by the auth client itself: AuthSessionMissingError,
│                                      AuthInvalidCredentialsError, AuthInvalidJwtError,
│                                      AuthImplicitGrantRedirectError, UserDoesNotExistError
├── StorageException                Root of the storage errors: VectorBucketException
├── FunctionsError                  Root of the functions errors.
├── RealtimeError                   Root of the realtime errors: NotConnectedError,
│                                   AuthorizationError, MaxRetriesExceeded
└── SupabaseException               The client was created with an invalid URL or key.
```

The response errors inherit both from the root of their package and from `SupabaseAPIError`, so `except AuthApiError` and `except AuthError` keep working. Arguments the client rejects before sending a request raise the built-in `ValueError` or `TypeError`, as they do everywhere in Python, except for a vector batch of the wrong size, which raises `VectorBucketException`.

## Important: Proper Client Shutdown

To ensure the Supabase client terminates correctly and to prevent resource leaks, you **must** explicitly call:

```python
client.auth.sign_out()
```
