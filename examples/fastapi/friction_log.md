# supabase-py Friction Log

Issues discovered while building the FastAPI Realtime Rule Engine example.
Append entries as they are found during implementation.

---

## Per-request JWT injection is not ergonomic

**Severity:** medium
**Where:** `dependencies.py` / `AsyncClientOptions`
**What happened:** Passing `headers={...}` to `AsyncClientOptions(headers={...})`
replaces the entire default dict, silently dropping `X-Client-Info` and any
other default headers. The correct pattern is to construct `AsyncClientOptions()`
and then mutate `.headers["Authorization"]` — but this is not documented and not
obvious from the constructor signature.
**Recommendation:** Add a `with_auth(token: str) -> AsyncClientOptions` factory
method that returns a copy of the default options with only the Authorization
header overridden, making the per-request pattern a one-liner.

---

## Manual connect() required before subscribe()

**Severity:** medium
**Where:** `engine.py:start_engine` / `AsyncRealtimeClient`
**What happened:** Calling `channel.subscribe()` without first calling
`service_client.realtime.connect()` results in the subscription silently
failing or raising. There is no auto-connect behavior.
**Recommendation:** Either auto-connect when the first `channel.subscribe()`
is called (matching the JS SDK behavior), or raise an explicit error with a
clear message if `subscribe()` is called before `connect()`.

---

## Realtime callback async support is undocumented

**Severity:** high
**Where:** `engine.py` / `channel.on_postgres_changes(callback=...)`
**What happened:** It is unclear from the SDK docs or type annotations whether
`on_postgres_changes` accepts an async callable. The sync wrapper with
`asyncio.create_task()` is a workaround discovered by trial and error.
**Recommendation:** Add explicit support for async callbacks in
`on_postgres_changes` (detect with `asyncio.iscoroutinefunction`) and document
this in the method docstring and README.

---

## Broadcast requires a prior subscribe() on the channel

**Severity:** high
**Where:** `engine.py:on_task_change` / `channel.send()`
**What happened:** Calling `channel.send()` on a freshly created channel without
first calling `channel.subscribe()` either raises or silently no-ops. Creating
and subscribing a new channel per broadcast event is expensive and semantically
odd (subscribing implies receiving, but we only want to send).
**Recommendation:** Add a `channel.broadcast(event, payload)` method that
connects and sends without requiring a full subscription lifecycle, matching the
common server-side fire-and-forget pattern.

---

## Per-request AsyncClient construction is expensive and unguided

**Severity:** high
**Where:** `dependencies.py:get_client`
**What happened:** Every HTTP request constructs a new `AsyncClient` via
`acreate_client()`, which initialises an httpx `AsyncClient`, a new auth client,
lazy postgrest/storage/functions clients, and wires up the `_listen_to_auth_events`
callback. There is no supported pattern for sharing an httpx session across
requests while varying the Authorization header.
**Recommendation:** Provide a `AsyncClient.with_token(jwt: str) -> AsyncClient`
method that returns a lightweight copy sharing the underlying httpx session but
with a different auth header — making per-request JWT injection cheap and
idiomatic.

---

## Realtime payload key mismatch vs JS SDK

**Severity:** high
**Where:** `engine.py:on_task_change` / `payload` argument from `on_postgres_changes`
**What happened:** The JS Supabase client normalizes the Realtime payload to
`payload.new` and `payload.old` for the changed records. `supabase-py` does NOT
perform this normalization — the raw server format is used instead, where the new
record is at `payload["data"]["record"]` and the old record is at
`payload["data"]["old_record"]`. Code ported from JS examples that uses
`payload["new"]` silently gets an empty dict (no KeyError) and returns early,
producing zero rule events with no error logged.
**Recommendation:** Normalize the Realtime Postgres Changes payload to match the
JS SDK shape (`payload["new"]`, `payload["old"]`) so that documentation examples
and cross-SDK code work without modification. Alternatively, document the difference
prominently in the API reference.

---

## `auth.sign_up()` on a service-role client corrupts its auth state

**Severity:** high
**Where:** `tests/e2e/conftest.py` / any code that calls `auth.sign_up()` or `auth.sign_in()`
**What happened:** Calling `client.auth.sign_up(...)` on a `service_role` client
stores the new user's session in the client's internal auth state, overwriting the
service role key. Subsequent requests from that client use the user's JWT instead
of the service key, causing `auth.admin.*` calls to return 403 "User not allowed".
This is a silent mutation with no warning — the client appears functional until a
privileged operation fails.
**Recommendation:** Document that service-role clients must not be used for
sign-up or sign-in operations. Raise a warning (or error) if `auth.sign_up()` is
called on a client initialized with a service-role key. Alternatively, store the
admin key separately from the session so it cannot be overwritten.

---

## Service role vs anon key have no type-level distinction

**Severity:** medium
**Where:** `main.py` / `engine.py` / any file that creates a client
**What happened:** Both the service role client and the per-request anon client
are `AsyncClient` instances. It is easy to pass the wrong one to a function,
accidentally bypassing RLS or exposing the service key to user-controlled inputs.
**Recommendation:** Introduce `ServiceRoleClient` and `AnonClient` subclasses (or
typed wrappers) so that type checkers can catch misuse, and document clearly which
methods require which client type.
