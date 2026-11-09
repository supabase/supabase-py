# Migrating from v2 to v3

## Spelled out abbreviations in public names

Abbreviated and contracted public names are spelled out. Wire formats do not change.

| Package              | Before                                                           | After                                                                                 |
| -------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `realtime`           | `connect_once(hb_interval=..., hb_timeout=...)`                  | `connect_once(heartbeat_interval=..., heartbeat_timeout=...)`                         |
| `realtime`           | `RealtimeClient(ws_connection, hb_interval=..., hb_timeout=...)` | `RealtimeClient(websocket_connection, heartbeat_interval=..., heartbeat_timeout=...)` |
| `realtime`           | `RealtimeClient.hb_interval`                                     | `RealtimeClient.heartbeat_interval`                                                   |
| `realtime`           | `connect_once.ws`                                                | `connect_once.websocket`                                                              |
| `realtime`           | `RealtimeClient.channel(topic, params=...)`                      | `RealtimeClient.channel(topic, options=...)`                                          |
| `realtime`           | `RealtimeChannel(socket, topic, params=...)`                     | `RealtimeChannel(socket, topic, options=...)`                                         |
| `realtime`           | `RealtimeChannel.params`                                         | `RealtimeChannel.options`                                                             |
| `realtime`           | `PresenceOpts`                                                   | `PresenceOptions`                                                                     |
| `realtime`           | `VSN`                                                            | `PROTOCOL_VERSION`                                                                    |
| `supabase`           | `RealtimeClientOptions` keys `hb_interval`, `hb_timeout`         | `heartbeat_interval`, `heartbeat_timeout`                                             |
| `supabase`           | `AClient`                                                        | `AsyncClient`                                                                         |
| `supabase`           | `ASupabaseException`                                             | `SupabaseException`                                                                   |
| `supabase`           | `ASupabaseStorageClient`                                         | `storage3.AsyncStorageClient`                                                         |
| `supabase`           | `httpx.create_aclient`, `aiohttp.create_aclient`                 | `httpx.create_async_client`, `aiohttp.create_async_client`                            |
| `supabase_auth`      | `UserDoesntExist`                                                | `UserDoesNotExistError`                                                               |
| `supabase_auth`      | `helpers.validate_exp(exp)`                                      | `helpers.validate_expiration(expires_at)`                                             |
| `supabase_auth`      | `admin.get_user_by_id(uid)`                                      | `admin.get_user_by_id(user_id)`                                                       |
| `supabase_auth`      | `admin.update_user_by_id(uid, attributes)`                       | `admin.update_user_by_id(user_id, attributes)`                                        |
| `storage3`           | `VectorBucketException(msg)`, `.msg`                             | `VectorBucketException(message)`, `.message`                                          |
| `supabase_functions` | `utils.is_valid_str_arg`                                         | `utils.is_valid_string_argument`                                                      |
| `supabase_utils`     | `Headers.set(key, val)`, `Headers.override(key, val)`            | `Headers.set(key, value)`, `Headers.override(key, value)`                             |
| `supabase_utils`     | `URLQuery.set(key, val)`                                         | `URLQuery.set(key, value)`                                                            |

Names that mirror a wire format keep their wire spelling, for example the JWT claims on `JWTPayload` and the realtime `ref` and `join_ref` message fields. Acronyms such as `JWT`, `MFA`, `OTP`, `SSO` and `URL`, the PostgREST filter operators, and Python idioms such as `params` and `kwargs` are unchanged.

## Storage `upsert` is a `bool`

`upsert` is a keyword argument that takes a `bool`. It is sent as the `x-upsert` header. Passing a string raises `TypeError`.

| Before                                                       | After                                         |
| ------------------------------------------------------------ | --------------------------------------------- |
| `upload(path, file, file_options={"upsert": "true"})`        | `upload(path, file, upsert=True)`             |
| `create_signed_upload_url(path, options={"upsert": "true"})` | `create_signed_upload_url(path, upsert=True)` |
| `update(path, file, file_options={"upsert": "true"})`        | `update(path, file)`                          |

`update()` no longer takes `upsert`. It never sent the header, so the option had no effect.

## One implementation for `AsyncClient` and `Client`

`AsyncClient` and `Client` are defined in `supabase.client` over a shared base. The `supabase._async` and `supabase._sync` modules are removed, and so are the extra names that pointed at the same classes.

| Before                                            | After                                                 |
| ------------------------------------------------- | ----------------------------------------------------- |
| `from supabase._async.client import AsyncClient`  | `from supabase import AsyncClient`                    |
| `from supabase._sync.client import Client`        | `from supabase import Client`                         |
| `AsyncSupabaseException`, `SyncSupabaseException` | `SupabaseException`                                   |
| `supabase.SupabaseStorageClient`                  | `storage3.SyncStorageClient`                          |
| `supabase.client.AsyncSupabaseStorageClient`      | `storage3.AsyncStorageClient`                         |
| `client.rpc("fn", {"a": 1}, CountMethod.exact)`   | `client.rpc("fn", {"a": 1}, count=CountMethod.exact)` |
| `client.rpc("fn", {"a": 1}, None, True)`          | `client.rpc("fn", {"a": 1}, head=True)`               |

`rpc` takes `head`, `count` and `get` as keyword arguments, like `PostgrestClient.rpc`. `params` stays the second positional argument.

`SupabaseException` is one class, so `except SupabaseException` also catches errors raised by `AsyncClient`.

## Client options are keyword arguments

`ClientOptions`, `AsyncClientOptions`, their v2 names `SyncClientOptions` and `AClientOptions`, and the `supabase.lib.client_options` module are removed. `create_client`, `create_async_client`, `Client`, `AsyncClient` and their `create` methods take the settings as keyword-only arguments. Settings that apply to every service are arguments of their own. The settings of one service are grouped in an options class, passed in the argument named after the service.

```python
client = create_client(
    url,
    key,
    headers={"x-app": "1"},
    request_timeout=30,
    postgrest=PostgrestClientOptions(schema="private"),
    auth=AuthClientOptions(flow_type="implicit", session_storage=my_storage),
    storage=StorageClientOptions(request_timeout=120),
)
```

| Before                                                         | After                                                              |
| -------------------------------------------------------------- | ------------------------------------------------------------------ |
| `create_client(url, key, http_client)`                         | `create_client(url, key, http_client=http_client)`                 |
| `ClientOptions(headers={"x-app": "1"})`                        | `headers={"x-app": "1"}`                                           |
| `ClientOptions(request_timeout=30)`                            | `request_timeout=30`                                               |
| `ClientOptions(schema="private")`                              | `postgrest=PostgrestClientOptions(schema="private")`               |
| `ClientOptions(auto_refresh_token=False)`                      | `auth=AuthClientOptions(auto_refresh_token=False)`                 |
| `ClientOptions(storage=my_storage)`                            | `auth=AuthClientOptions(session_storage=my_storage)`               |
| `ClientOptions(flow_type="implicit")`                          | `auth=AuthClientOptions(flow_type="implicit")`                     |
| `ClientOptions(persist_session=False)`                         | Leave it out                                                       |
| `ClientOptions(postgrest_options=PostgrestClientOptions(...))` | `postgrest=PostgrestClientOptions(...)`                            |
| `ClientOptions(auth_options=AuthClientOptions(...))`           | `auth=AuthClientOptions(...)`                                      |
| `ClientOptions(storage_options=StorageClientOptions(...))`     | `storage=StorageClientOptions(...)`                                |
| `ClientOptions(functions_options=FunctionsClientOptions(...))` | `functions=FunctionsClientOptions(...)`                            |
| `AsyncClientOptions(realtime=RealtimeClientOptions(...))`      | `realtime=RealtimeClientOptions(...)`                              |
| `client.options.headers`                                       | `client.headers`                                                   |
| `options.replace(schema="other")`                              | `postgrest=dataclasses.replace(postgrest_options, schema="other")` |

`AuthClientOptions.session_storage` takes an `AsyncSupportedStorage` for `AsyncClient` and a `SyncSupportedStorage` for `Client`. It used to be called `storage`, which clashed with the storage service. Left out, the session is kept in memory.

`persist_session` is removed. It was never passed on to the session manager, so it had no effect. To keep the session only in memory, leave `session_storage` out.

`headers` are sent on top of the default `X-Client-Info` header instead of replacing it. A header you pass with the same name, in any case, still replaces the default one.

`client.headers` is a read-only view of the headers sent with every request. Its `Authorization` header follows the session. The headers you pass are copied, so changing the original dictionary later has no effect.

`PostgrestClientOptions`, `AuthClientOptions`, `StorageClientOptions` and `FunctionsClientOptions` take keyword arguments only.

## Options are dataclasses instead of dictionaries

The remaining option `TypedDict`s are dataclasses. Fields you leave out use the same defaults as before.

| Package    | Before                                                       | After                                                                                  |
| ---------- | ------------------------------------------------------------ | -------------------------------------------------------------------------------------- |
| `supabase` | `AsyncClientOptions(realtime={"heartbeat_interval": 30})`    | `create_async_client(url, key, realtime=RealtimeClientOptions(heartbeat_interval=30))` |
| `storage3` | `list_v2(sort_by={"column": "created_at", "order": "desc"})` | `list_v2(sort_by=SortByV2(column="created_at", order="desc"))`                         |

`RealtimeClientOptions` is exported from `supabase`, and `SortByV2` from `storage3.types`.

The unused `storage3.types.SearchV2Options` and `storage3.types.UploadData` are removed.

## Options are frozen

Option and parameter dataclasses are frozen. Setting a field raises `dataclasses.FrozenInstanceError`. Build a changed copy with `dataclasses.replace` instead.

This covers `PostgrestClientOptions`, `AuthClientOptions`, `StorageClientOptions`, `FunctionsClientOptions`, `RealtimeClientOptions`, `realtime.RealtimeChannelOptions`, `realtime.PostgresChangesBinding`, the `storage3.types` `SortByType`, `SortByV2` and `TransformOptions`, and the `supabase_auth` credential and parameter classes such as `SignUpWithEmailAndPasswordCredentials` and `VerifyEmailOtpParams`.

| Before                                                 | After                                                    |
| ------------------------------------------------------ | -------------------------------------------------------- |
| `options.schema = "other"`                             | `options = dataclasses.replace(options, schema="other")` |
| `options.broadcast(ack=True)` without using the result | `options = options.broadcast(ack=True)`                  |
| `options.postgres_changes_bindings.append(binding)`    | `options = options.postgres_changes(...)`                |

The `RealtimeChannelOptions` builder methods return a new copy and leave the original unchanged, so chained calls keep working. `postgres_changes_bindings` and `PostgresChangesBinding.select` are stored as tuples.

The client constructors of `supabase_auth`, `postgrest`, `storage3` and `supabase_functions` accept any `Mapping` for `headers`, not only a `dict`.

## Realtime heartbeat intervals are used as given

`heartbeat_interval` was raised to 15 seconds when it was lower. It is now used as given, so an interval below 15 seconds sends heartbeats more often than before. To keep the old timing, pass 15 or more.

`heartbeat_interval` and `heartbeat_timeout` are typed `float` and are in seconds. `connect_once`, `RealtimeClient` and `RealtimeClientOptions` raise `ValueError` when either one is not positive.

## Auth `persist_session` is removed and `storage_key` takes effect

`AsyncSupabaseAuthClient` and `SyncSupabaseAuthClient` no longer take `persist_session`. It was never passed on to the session manager, so it had no effect. To keep the session only in memory, leave `storage` out. Each client then gets its own memory storage, so clients created per request do not share a session.

`storage_key` was accepted but ignored as well. It is now the key the session is stored under, with the PKCE code verifier under `<storage_key>-code-verifier`. Set it on `AuthClientOptions` or on the auth client constructors to keep clients that share a storage apart.

- Sessions saved before the upgrade are under `supabase.auth.token`, the default. Leave `storage_key` out to keep reading them.
- `storage_key` is typed `str`. Passing `None` is no longer accepted.

## Request timeouts

`AsyncStorageClient` and `SyncStorageClient` no longer take a `timeout` parameter. It was ignored. Pass `request_timeout` as a keyword argument instead.

| Before                                         | After                                                          |
| ---------------------------------------------- | -------------------------------------------------------------- |
| `SyncStorageClient(url, headers, session, 20)` | `SyncStorageClient(url, headers, session, request_timeout=20)` |

`request_timeout` is in seconds and limits how long a request may go without progress. Set it with the `request_timeout` argument of the client for every service, on `PostgrestClientOptions`, `AuthClientOptions`, `StorageClientOptions` or `FunctionsClientOptions` for one service, with `request_timeout()` on a database query, or with the `request_timeout` argument of `functions.invoke()`. None, the default, leaves the timeout to the HTTP client.

A timed-out request raises `supabase.RequestTimeoutError`, a subclass of the built-in `TimeoutError`, instead of an httpx or aiohttp exception. This also applies to timeouts configured on the HTTP client.

## One exception hierarchy

Every exception the packages raise themselves inherits from `supabase_utils.errors.SupabaseError`, re-exported as `supabase.SupabaseError`, so `except SupabaseError` catches any failure the SDK reports. The hierarchy is described in the [error handling](src/supabase/README.md#error-handling) section of the README. The realtime connection is the exception: a lost websocket still surfaces as the `websockets.ConnectionClosed` or built-in `TimeoutError` that failed it, as before.

Errors a service answered with inherit from `SupabaseAPIError` and expose the HTTP status as `status_code`, with the `response` next to it. The `status` attributes are renamed and the constructors take the status as a keyword argument.

| Package              | Before                                                      | After                                                                                                                                |
| -------------------- | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `supabase_auth`      | `AuthApiError.status`                                       | `AuthApiError.status_code`                                                                                                           |
| `supabase_auth`      | `AuthUnknownError.status`, `AuthUnknownError.data`          | `AuthUnknownError.status_code`, `AuthUnknownError.response.content`                                                                  |
| `supabase_auth`      | `AuthRetryableError(message, status)`                       | `AuthRetryableError(message, status_code=...)`, a subclass of `AuthApiError`                                                         |
| `supabase_auth`      | `AuthWeakPasswordError(message, status, reasons)`           | `AuthWeakPasswordError(message, status_code=..., reasons=...)`, a subclass of `AuthApiError`                                         |
| `supabase_auth`      | `CustomAuthError`, `.status` on its subclasses              | Removed. `AuthSessionMissingError` and the other errors the client raises on its own inherit `AuthError` directly and have no status |
| `postgrest`          | `APIError(error)`                                           | `APIError(error, status_code=..., response=...)`, with `status_code` and `response` attributes                                       |
| `postgrest`          | `str(error)` was the error dictionary                       | `str(error)` is the error message, `error.json()` is the dictionary                                                                  |
| `storage3`           | `StorageApiError(message=..., code=..., status=...)`        | `StorageApiError(message, status_code=..., code=..., response=...)`                                                                  |
| `storage3`           | `StorageApiError.status`                                    | `StorageApiError.status_code`                                                                                                        |
| `supabase_functions` | `FunctionsError(message, name, status)`, `.name`, `.status` | `FunctionsError(message)`. Use `type(error).__name__` for the name; the status lives on the response errors                          |
| `supabase_functions` | `FunctionsHttpError(message, code)`, `.status`              | `FunctionsHttpError(message, status_code=..., response=...)`, `.status_code`                                                         |
| `supabase_functions` | `FunctionsRelayError(message, code)`, `.status`             | `FunctionsRelayError(message, status_code=..., response=...)`, `.status_code`                                                        |
| `realtime`           | `realtime.client.MaxRetriesExceeded`, an `Exception`        | `realtime.MaxRetriesExceeded`, a `RealtimeError` with a `retries` attribute                                                          |
| `realtime`           | A failed `subscribe()` raised `Exception`                   | It raises `RealtimeError`                                                                                                            |

The auth errors are no longer dataclasses. `str(error)` returns the message for every error, as it does for the built-in exceptions, and `==` compares identity.

A request that fails before a response can be read, because the connection failed, the request timed out or the HTTP client gave up on a redirect loop, raises `supabase.SupabaseTransportError` instead of an httpx or aiohttp exception, with that exception chained as `__cause__`. `RequestTimeoutError` is a subclass of it, and still a subclass of the built-in `TimeoutError`. Code that caught `httpx.ConnectError` or `aiohttp.ClientConnectorError` around a call of the SDK should catch `SupabaseTransportError` instead. The outcome of such a request is unknown, since it may have reached the service.
