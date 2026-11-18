# `supabase-py`

Python client for [Supabase](https://supabase.com)

- Documentation: [supabase.com/docs](https://supabase.com/docs/reference/python/introduction)
- Usage:
  - [GitHub OAuth in your Python Flask app](https://supabase.com/blog/oauth2-login-python-flask-apps)
  - [Python data loading with Supabase](https://supabase.com/blog/loading-data-supabase-python)

### PyPI installation

Install the package (for Python >= 3.12):

```bash
# with pip
pip install supabase

# with uv
uv add supabase

# with conda
conda install -c conda-forge supabase
```

The client sends its requests with httpx. To run the async client on aiohttp instead, install `supabase[aiohttp]` and use `create_async_client` from `supabase.aiohttp`.

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

Listing objects with `list()` needs Supabase Storage v1.19.0 or newer, which added `POST /object/list-v2`.

## Usage

Set your Supabase environment variables in a dotenv file, or using the shell:

```bash
export SUPABASE_URL="my-url-to-my-awesome-supabase-instance"
export SUPABASE_KEY="my-supa-dupa-secret-supabase-api-key"
```

Init client:

```python
import os
from supabase import Client, create_client

url: str = os.environ["SUPABASE_URL"]
key: str = os.environ["SUPABASE_KEY"]
supabase: Client = create_client(url, key)
```

`SUPABASE_URL` must be an `https` URL. Plain `http` is only accepted for a loopback host (`localhost`, `127.0.0.0/8` or `::1`), such as `http://localhost:54321` from the Supabase CLI, since it sends the API key and the session of the user in clear text. For any other host, such as an emulator, a LAN address or a Docker service name, pass `allow_insecure_http=True`:

```python
import os
from supabase import create_client

supabase = create_client(
    "http://192.168.1.20:54321",
    os.environ["SUPABASE_KEY"],
    allow_insecure_http=True,
)
```

For the async client, use `create_async_client`, which returns an `AsyncClient`:

```python
import asyncio
import os

from supabase import create_async_client


async def main() -> None:
    async with create_async_client(
        os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"]
    ) as supabase:
        response = await supabase.table("countries").select("*").execute()
        print(response.data)


asyncio.run(main())
```

Settings are keyword arguments. `headers` and `request_timeout` apply to the database, auth, storage and edge functions, not to the realtime connection of `AsyncClient`. The settings of one service are grouped in an options class:

```python
import os

from supabase import (
    AuthClientOptions,
    PostgrestClientOptions,
    StorageClientOptions,
    create_client,
)

supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"],
    headers={"x-app": "my-app"},
    request_timeout=30,
    postgrest=PostgrestClientOptions(schema="private"),
    auth=AuthClientOptions(flow_type="implicit"),
    storage=StorageClientOptions(request_timeout=120),
)
```

`request_timeout` is in seconds. The `request_timeout` of a service's options overrides the global one for that service. Without either, a request fails after 60 seconds without progress, with httpx and with aiohttp alike. An `http_client` you pass in keeps its own timeout instead.

`retry` is a `RetryPolicy`, exported from `supabase`, that says how a request that failed in a way worth repeating is retried. By default a GET or HEAD request is sent up to three more times on a rate limit, a gateway error or a network error, a timeout included, after the wait the service asked for with `Retry-After` or an exponential backoff with jitter. A response that asks for a longer wait than the `max_delay` of the policy, 30 seconds by default, is not retried. Writes are not retried unless you opt in with `retry(True)` on a query, or the `retry` argument of `functions.invoke()`, for a write that is safe to send twice. The `retry` of a service's options overrides the global one, and `RetryPolicy(max_retries=0)` turns retries off:

```python
import os

from supabase import RetryPolicy, StorageClientOptions, create_client

supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"],
    retry=RetryPolicy(max_retries=5, max_delay=60),
    storage=StorageClientOptions(retry=RetryPolicy(max_retries=0)),
)
supabase.table("countries").select("*").retry(False).execute()
```

### Secret and `service_role` keys

A client created with a secret key (`sb_secret_...`) or a legacy `service_role` key bypasses row level security. It keeps sending that key after a sign-in, so its data calls never switch to the signed in user. Do not sign users in on such a client. Use a separate client created with the publishable key, or `with_token()` to act for a user.

### One client per request on a server

A server such as a FastAPI or Django app acts for the user who sent the request, so that row level security applies to them. Create one client when the app starts and call `with_token()` with the user's JWT in each request. It returns a client that shares the HTTP connections, headers and options of the first one, and only differs in the `Authorization` header. It does no I/O, so creating one per request is cheap. It never refreshes or replaces the token, and leaving it with `async with` does not close the shared connections. It has no auth client, so using its `auth` raises `SupabaseException`.

```python
import os

from supabase import create_async_client

shared = create_async_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])


async def list_todos(access_token: str) -> object:
    response = (
        await shared.with_token(access_token).table("todos").select("*").execute()
    )
    return response.data
```

In FastAPI, read the token with the `HTTPBearer` security dependency, which parses the `Authorization` header and rejects a request without one, and create `shared` with `async with` in the lifespan of the app, so that it is closed when the app shuts down. To check the token, use `shared.auth.get_claims(access_token)`, which caches the signing keys of the project between requests.

Use the supabase client to interface with your database.

### Sign-up

```python
from supabase_auth import SignUpWithPassword

response = supabase.auth.sign_up(
    SignUpWithPassword.email("someone@example.com", "a-strong-password")
)
```

### Sign-in

```python
from supabase_auth import SignInWithPassword

response = supabase.auth.sign_in_with_password(
    SignInWithPassword.email("someone@example.com", "a-strong-password")
)
```

### Complete a sign-in after a redirect

With the default PKCE flow, OAuth, SSO, magic link and password reset sign-ins redirect to your app with a `code`. Pass the full callback URL to `initialize_from_url`: it exchanges the code for a session and reads the tokens of the implicit flow. When the URL carries an `error`, `error_code` or `error_description` instead, it raises `AuthImplicitGrantRedirectError`. A failed sign-in keeps the stored session. Several of these flows can be pending at once, for example in two tabs. With `append_flow_id_to_redirects`, every redirect URL you pass, such as `redirect_to` or `email_redirect_to`, also gets a `sb_flow_id` query parameter that tells the callback which flow it completes. Allow the parameter in the redirect URL allow list of your project first, for example with `https://example.com/callback**`, since an entry without a wildcard no longer matches the URL.

```python
import os

from supabase import AuthClientOptions, create_client

supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"],
    auth=AuthClientOptions(append_flow_id_to_redirects=True),
)


def callback(url: str) -> None:
    supabase.auth.initialize_from_url(url)
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

### Reuse a query

Every builder method returns a new query and leaves the original unchanged, so one base query can branch into several requests. Each request sends only its own filters.

```python
asian_countries = supabase.table("countries").select("id", "name").eq("continent", "Asia")
large = asian_countries.gte("population", 100_000_000).execute()
small = asian_countries.lt("population", 1_000_000).execute()
```

### Update Data

```python
data = supabase.table("countries").update({"country": "Indonesia", "capital_city": "Jakarta"}).eq("id", 1).execute()
```

An update or a delete without a filter would affect every row in the table, so executing one raises `ValueError` before anything is sent. To affect every row on purpose, call `all()`:

```python
data = supabase.table("countries").update({"visited": False}).all().execute()
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
data = supabase.table("countries").delete().all().execute()
```

### Call Edge Functions

```python
from supabase import FunctionsHttpError, FunctionsRelayError

try:
    response = supabase.functions.invoke("hello-world", body={"name": "Functions"})
    print(response.content)
except (FunctionsRelayError, FunctionsHttpError) as error:
    print(error.status_code, error.message)
```

`invoke_stream()` reads the response of a function that streams, such as one that sends server-sent events, as it arrives. It takes the arguments of `invoke()` and gives a response whose body is read once with `iter_text()`, `iter_events()`, `read()` or by iterating over its chunks:

```python
with supabase.functions.invoke_stream("chat", body={"prompt": "Hello"}) as response:
    for event in response.iter_events():
        print(event.event, event.data)
```

### Download a file from Storage

```python
bucket_name: str = "photos"

data = supabase.storage.from_(bucket_name).download("photo1.png")
```

### Upload a file

```python
from pathlib import Path

bucket_name: str = "photos"

data = supabase.storage.from_(bucket_name).upload(
    "user1/profile.png", Path("profile.png"), content_type="image/png"
)
```

### Remove a file

```python
bucket_name: str = "photos"

data = supabase.storage.from_(bucket_name).remove(["old_photo.png", "image5.jpg"])
```

### List files

`list()` returns one page. With `with_delimiter=True` it lists one level, with the folders apart from the objects. Pass the `nextCursor` of a page to fetch the next one, or let `pages()` follow the cursors, fetching each page only when the loop reaches it. On the async client, loop over it with `async for`.

```python
bucket_name: str = "charts"

bucket = supabase.storage.from_(bucket_name)
for page in bucket.pages("2024/", with_delimiter=True):
    print(page.folders, page.objects)
```

### List buckets

`list_buckets()` returns every bucket. Pass `limit` and `offset` to page through them, `search` to filter them by name, and `sort_column` and `sort_order` to sort them.

```python
buckets = supabase.storage.list_buckets(
    limit=10, offset=0, search="photo", sort_column="created_at", sort_order="desc"
)
```

### Move and rename files

```python
bucket_name: str = "charts"
old_file_path: str = "generic/graph1.png"
new_file_path: str = "important/revenue.png"

data = supabase.storage.from_(bucket_name).move(old_file_path, new_file_path)
```

### Listen to realtime messages

`AsyncClient.realtime` is one realtime client per `AsyncClient`. It connects when the first channel subscribes, all its channels share that connection, and the connection is closed when the last channel is unsubscribed or the `AsyncClient` exits. A client that never subscribes opens no connection. Channels join with the access token of the current session, read through `auth.get_session()` so that an expiring session is refreshed first, and a new token is sent to them as soon as the user signs in, the session refreshes or the user signs out. The sync `Client` has no realtime client.

```python
import os

from realtime import BroadcastMessage
from supabase import create_async_client

async with create_async_client(
    os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"]
) as async_supabase:
    async with async_supabase.realtime.channel("room") as channel:
        async for message in channel.messages:
            if isinstance(message, BroadcastMessage):
                print(message.payload)
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
├── AuthError                       Root of the auth errors. Raised by the auth client itself as
│                                   AuthSessionMissingError, AuthInvalidCredentialsError,
│                                   AuthInvalidJwtError, AuthImplicitGrantRedirectError,
│                                   UserDoesNotExistError
├── StorageException                Root of the storage errors: VectorBucketException
├── FunctionsError                  Root of the functions errors.
├── RealtimeError                   Root of the realtime errors: NotConnectedError,
│   │                               RealtimeTimeoutError, also a built-in `TimeoutError`.
│   └── ChannelJoinError               The server rejected a join. `reason` and `code` say why.
│       └── AuthorizationError            The token, or the RLS policies of a private channel.
└── SupabaseException               The client was created with an invalid URL or key, or `auth`
                                    was used on a `with_token()` client.
```

The response errors inherit both from the root of their package and from `SupabaseAPIError`, so `except AuthApiError` and `except AuthError` keep working. Arguments the client rejects before sending a request raise the built-in `ValueError` or `TypeError`, as they do everywhere in Python, except for a vector batch of the wrong size, which raises `VectorBucketException`. A send on a lost realtime connection raises the `websockets.ConnectionClosed` or built-in `TimeoutError` that failed it, not a `SupabaseError`. The realtime client reconnects on its own and joins its channels again.

## Logging

Every package logs through the standard `logging` module under the `supabase` logger: `supabase.http` for requests and retries, `supabase.auth` for the session refresh, `supabase.realtime` for the realtime connection, `supabase.realtime.websockets` for its websocket frames and `supabase.client` for the client. The packages only add a `NullHandler`, so nothing is printed until you configure logging. Each request is logged at `DEBUG` with its method, path, status and duration in seconds, which are also set on the log record as the `http_method`, `http_path`, `http_status` and `duration` attributes for structured formatters:

```python
import logging

logging.basicConfig()
logging.getLogger("supabase").setLevel(logging.DEBUG)
```

Setting the `SUPABASE_LOG` environment variable to `debug`, `info`, `warning` or `error` does the same without code, printing the logs of that level and above to standard error. The `supabase` logs never contain keys, tokens, header values, query strings or the bodies of requests and messages. The HTTP clients have loggers of their own outside it: httpx logs every request at `INFO` under the `httpx` logger with its full URL, query string included. Raise its level when you log at `INFO` or below:

```python
import logging

logging.getLogger("httpx").setLevel(logging.WARNING)
```

## Closing the client

The client keeps its HTTP connections open and refreshes the session in the background. Use it as a context manager, or call `close()`, to stop the refresh and close the connections when you are done:

```python
import os

from supabase import create_client

with create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"]) as supabase:
    data = supabase.table("countries").select("*").execute()
```

`AsyncClient` works the same way with `async with` or `await supabase.aclose()`. Closing the client closes the HTTP client that `create_client` created, but not an `http_client` you passed in, which stays yours to close. It also closes the realtime connection of `AsyncClient.realtime`.
