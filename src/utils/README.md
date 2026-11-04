# supabase_utils

The shared HTTP layer of the supabase-py packages. `supabase_functions`, `supabase_auth`, `postgrest`, `storage3` and `supabase` all build on it, so each of them can be used with the HTTP client of your choice, synchronously or asynchronously, without depending on that client.

Most users do not use this package directly. Install it with the extra for the HTTP client you want to use next to the package you use:

```bash
pip install supabase_functions "supabase_utils[httpx]"
# or
pip install supabase_functions "supabase_utils[aiohttp]"
```

| Extra     | Adapters                            | Mode        |
| --------- | ----------------------------------- | ----------- |
| `httpx`   | `HttpxSession`, `AsyncHttpxSession` | sync, async |
| `aiohttp` | `AsyncAiohttpSession`               | async       |
| `all`     | all of the above                    | sync, async |

## Using an adapter

Wrap a client of the HTTP library in an adapter and hand it to a package. Leaving the adapter's context manager closes the client:

```python
from httpx import AsyncClient, Client
from supabase_functions import AsyncFunctionsClient, SyncFunctionsClient
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession

with HttpxSession(Client()) as session:
    functions = SyncFunctionsClient(
        "https://<project_ref>.functions.supabase.co",
        {"Authorization": "Bearer <key>"},
        http_session=session,
    )
    functions.invoke("hello")

async with AsyncHttpxSession(AsyncClient()) as session:
    functions = AsyncFunctionsClient(
        "https://<project_ref>.functions.supabase.co",
        {"Authorization": "Bearer <key>"},
        http_session=session,
    )
    await functions.invoke("hello")
```

The aiohttp adapter works the same way:

```python
from aiohttp import ClientSession
from supabase_utils.http.adapters.aiohttp import AsyncAiohttpSession

async with AsyncAiohttpSession(ClientSession()) as session:
    ...
```

## How it works

The packages never call an HTTP library themselves. Each operation is a generator that yields a description of the request it wants to send, receives the `Response`, and returns its result:

```python
from typing import Generic

from supabase_utils.http.headers import Headers
from supabase_utils.http.io import HttpIO, HttpMethod, handle_http_io
from supabase_utils.http.request import EmptyRequest
from yarl import URL


class ItemsClient(Generic[HttpIO]):
    def __init__(self, executor: HttpIO, base_url: URL, default_headers: Headers) -> None:
        self.executor: HttpIO = executor
        self.base_url = base_url
        self.default_headers = default_headers

    @handle_http_io
    def get_item(self, item_id: str) -> HttpMethod[bytes]:
        response = yield EmptyRequest(path=["items", item_id], method="GET")
        return response.content
```

`handle_http_io` hands the generator to the client's `executor`, which joins each request path to `base_url` and merges `default_headers` into its headers. `SyncHttpIO` runs it with an `HttpSession` and returns the result, `AsyncHttpIO` runs it with an `AsyncHttpSession` and returns an awaitable. The same method therefore backs both the `Sync*` and the `Async*` client of a package.

The main modules are:

| Module                         | Contents                                                                                                                                        |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `supabase_utils.http.request`  | `Request` and `Response`, and the request builders `EmptyRequest`, `BytesRequest`, `JSONRequest`, `TextRequest` and `MultipartFormDataRequest`. |
| `supabase_utils.http.headers`  | `Headers`, an immutable, case insensitive multi map of header values.                                                                           |
| `supabase_utils.http.query`    | `URLQuery`, an immutable multi map of query parameters.                                                                                         |
| `supabase_utils.http.io`       | The `HttpSession` and `AsyncHttpSession` protocols, the `SyncHttpIO` and `AsyncHttpIO` executors and `handle_http_io`.                          |
| `supabase_utils.http.adapters` | The adapters for httpx and aiohttp.                                                                                                             |

## Writing an adapter

An adapter connects another HTTP library. It implements one of two protocols from `supabase_utils.http.io`:

- `HttpSession`: a `send(request) -> Response` method and the `__enter__` and `__exit__` methods of a context manager.
- `AsyncHttpSession`: an `async send(request) -> Response` method and the `__aenter__` and `__aexit__` methods of an async context manager.

`send` gets a fully built `Request`:

| Field     | Type            | Meaning                                                                     |
| --------- | --------------- | --------------------------------------------------------------------------- |
| `url`     | `yarl.URL`      | The absolute URL, query string included.                                    |
| `method`  | `str`           | `GET`, `POST`, `PATCH`, `PUT`, `DELETE` or `HEAD`.                          |
| `headers` | `Headers`       | The headers to send. `iter_items()` yields each value of a repeated header. |
| `content` | `bytes \| None` | The body, already encoded, or `None` for no body.                           |
| `delay`   | `float \| None` | Seconds to wait before sending. The executor waits, not the adapter.        |

It returns a `Response` with the status code, the body as `bytes`, the response headers and the request it answers. `send` must not raise for error statuses: the packages read `response.status` and raise their own errors. Errors of the transport itself, such as a refused connection, should propagate.

Leaving the context manager should close the underlying client.

A minimal adapter for the `requests` library:

```python
from types import TracebackType

import requests
from supabase_utils.http.headers import Headers
from supabase_utils.http.request import Request, Response


class RequestsSession:
    def __init__(self, session: requests.Session) -> None:
        self.session = session

    def send(self, request: Request) -> Response:
        response = self.session.request(
            method=request.method,
            url=str(request.url),
            headers=dict(request.headers),
            data=request.content,
        )
        return Response(
            status=response.status_code,
            content=response.content,
            headers=Headers.from_mapping(response.headers),
            request=request,
        )

    def __enter__(self) -> "RequestsSession":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.session.close()
```

`dict(request.headers)` joins the values of a repeated header with `, `. Pass `request.headers.iter_items()` instead if the library accepts a list of pairs, as httpx does.

The adapters in [`src/supabase_utils/http/adapters`](src/supabase_utils/http/adapters) are complete examples.

## Development

From the repository root:

```bash
make utils.tests   # pyrefly and pytest
```
