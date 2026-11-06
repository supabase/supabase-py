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
| `supabase`           | `AClient`, `AClientOptions`                                      | `AsyncClient`, `AsyncClientOptions`                                                   |
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
| `SyncClientOptions`                               | `ClientOptions`                                       |
| `supabase.SupabaseStorageClient`                  | `storage3.SyncStorageClient`                          |
| `supabase.client.AsyncSupabaseStorageClient`      | `storage3.AsyncStorageClient`                         |
| `client.rpc("fn", {"a": 1}, CountMethod.exact)`   | `client.rpc("fn", {"a": 1}, count=CountMethod.exact)` |
| `client.rpc("fn", {"a": 1}, None, True)`          | `client.rpc("fn", {"a": 1}, head=True)`               |

`ClientOptions` configures `Client` and `AsyncClientOptions` configures `AsyncClient`. `supabase.lib.client_options.ClientOptions` used to be their shared base class and is now the sync options class as well.

`rpc` takes `head`, `count` and `get` as keyword arguments, like `PostgrestClient.rpc`. `params` stays the second positional argument.

`SupabaseException` is one class, so `except SupabaseException` also catches errors raised by `AsyncClient`.

## Options are dataclasses instead of dictionaries

The remaining option `TypedDict`s are dataclasses. Fields you leave out use the same defaults as before.

| Package    | Before                                                       | After                                                                       |
| ---------- | ------------------------------------------------------------ | --------------------------------------------------------------------------- |
| `supabase` | `AsyncClientOptions(realtime={"heartbeat_interval": 30})`    | `AsyncClientOptions(realtime=RealtimeClientOptions(heartbeat_interval=30))` |
| `storage3` | `list_v2(sort_by={"column": "created_at", "order": "desc"})` | `list_v2(sort_by=SortByV2(column="created_at", order="desc"))`              |

`RealtimeClientOptions` is exported from `supabase`, and `SortByV2` from `storage3.types`. `ClientOptions.realtime` and `AsyncClientOptions.realtime` default to `RealtimeClientOptions()` instead of `None`.

The unused `storage3.types.SearchV2Options` and `storage3.types.UploadData` are removed.

## Options are frozen

Option and parameter dataclasses are frozen. Setting a field raises `dataclasses.FrozenInstanceError`. Build a changed copy instead, with `replace()` on the client options or with `dataclasses.replace` on the others.

This covers `ClientOptions`, `AsyncClientOptions`, `RealtimeClientOptions`, `realtime.RealtimeChannelOptions`, `realtime.PostgresChangesBinding`, the `storage3.types` `SortByType`, `SortByV2` and `TransformOptions`, and the `supabase_auth` credential and parameter classes such as `SignUpWithEmailAndPasswordCredentials` and `VerifyEmailOtpParams`.

| Before                                                 | After                                                                  |
| ------------------------------------------------------ | ---------------------------------------------------------------------- |
| `options.headers["x-app"] = "1"`                       | `options = options.replace(headers={**options.headers, "x-app": "1"})` |
| `options.schema = "other"`                             | `options = options.replace(schema="other")`                            |
| `options.broadcast(ack=True)` without using the result | `options = options.broadcast(ack=True)`                                |
| `options.postgres_changes_bindings.append(binding)`    | `options = options.postgres_changes(...)`                              |

`ClientOptions.headers` is typed as a read-only `Mapping`. The options copy the headers they are given, so changing the original dictionary later has no effect. The client no longer changes the options it is given. When the session changes it replaces `client.options` with a copy that has the new `Authorization` header.

The `RealtimeChannelOptions` builder methods return a new copy and leave the original unchanged, so chained calls keep working. `postgres_changes_bindings` and `PostgresChangesBinding.select` are stored as tuples.

The client constructors of `supabase_auth`, `postgrest`, `storage3` and `supabase_functions` accept any `Mapping` for `headers`, not only a `dict`.

## Realtime heartbeat intervals are used as given

`heartbeat_interval` was raised to 15 seconds when it was lower. It is now used as given, so an interval below 15 seconds sends heartbeats more often than before. To keep the old timing, pass 15 or more.

`heartbeat_interval` and `heartbeat_timeout` are typed `float` and are in seconds. `connect_once`, `RealtimeClient` and `RealtimeClientOptions` raise `ValueError` when either one is not positive.

## Request timeouts

`AsyncStorageClient` and `SyncStorageClient` no longer take a `timeout` parameter. It was ignored. Pass `request_timeout` as a keyword argument instead.

| Before                                         | After                                                          |
| ---------------------------------------------- | -------------------------------------------------------------- |
| `SyncStorageClient(url, headers, session, 20)` | `SyncStorageClient(url, headers, session, request_timeout=20)` |

`request_timeout` is in seconds and limits how long a request may go without progress. Set it on `ClientOptions` for every service, on `PostgrestClientOptions`, `AuthClientOptions`, `StorageClientOptions` or `FunctionsClientOptions` for one service, with `request_timeout()` on a database query, or with the `request_timeout` argument of `functions.invoke()`. None, the default, leaves the timeout to the HTTP client.

A timed-out request raises `supabase.RequestTimeoutError`, a subclass of the built-in `TimeoutError`, instead of an httpx or aiohttp exception. This also applies to timeouts configured on the HTTP client.
