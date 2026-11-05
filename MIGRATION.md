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

`AsyncClient` and `Client` are defined in `supabase.client` over a shared base. The `supabase._async` and `supabase._sync` modules are removed.

| Before                                           | After                                                 |
| ------------------------------------------------ | ----------------------------------------------------- |
| `from supabase._async.client import AsyncClient` | `from supabase import AsyncClient`                    |
| `from supabase._sync.client import Client`       | `from supabase import Client`                         |
| `client.rpc("fn", {"a": 1}, CountMethod.exact)`  | `client.rpc("fn", {"a": 1}, count=CountMethod.exact)` |
| `client.rpc("fn", {"a": 1}, None, True)`         | `client.rpc("fn", {"a": 1}, head=True)`               |

`rpc` takes `head`, `count` and `get` as keyword arguments, like `PostgrestClient.rpc`. `params` stays the second positional argument.

`SupabaseException` is one class. `ASupabaseException`, `AsyncSupabaseException` and `SyncSupabaseException` are aliases of it, so `except SupabaseException` also catches errors raised by `AsyncClient`.
