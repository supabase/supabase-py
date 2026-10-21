<br />
<p align="center">
  <a href="https://supabase.io">
        <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/supabase/supabase/main/packages/common/assets/images/supabase-logo-wordmark--dark.svg">
      <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/supabase/supabase/main/packages/common/assets/images/supabase-logo-wordmark--light.svg">
      <img alt="Supabase Logo" width="300" src="https://raw.githubusercontent.com/supabase/supabase/main/packages/common/assets/images/logo-preview.jpg">
    </picture>
  </a>

  <h1 align="center">Supabase Realtime Client</h1>

  <h3 align="center">Send ephemeral messages with <b>Broadcast</b>, track and synchronize state with <b>Presence</b>, and listen to database changes with <b>Postgres Change Data Capture (CDC)</b>.</h3>

  <p align="center">
    <a href="https://supabase.com/docs/guides/realtime">Guides</a>
    ·
    <a href="https://supabase.com/docs/reference/python">Reference Docs</a>
    ·
    <a href="https://multiplayer.dev">Multiplayer Demo</a>
  </p>
</p>

# Overview

This client enables you to use the following Supabase Realtime's features:

- **Broadcast**: send ephemeral messages from client to clients with minimal latency. Use cases include sharing cursor positions between users.
- **Presence**: track and synchronize shared state across clients with the help of CRDTs. Use cases include tracking which users are currently viewing a specific webpage.
- **Postgres Change Data Capture (CDC)**: listen for changes in your PostgreSQL database and send them to clients.

# Usage

## Installing the Package

```bash
pip3 install realtime
```

or using `uv`

```bash
uv add realtime
```

## Creating a Channel

```python
import asyncio

from realtime import connect_once

REALTIME_URL = "http://localhost:54321/realtime/v1"
API_KEY = "your-publishable-key"


async def get_token() -> str:
    return API_KEY


async def main() -> None:
    async with connect_once(REALTIME_URL, get_token) as client:
        async with client.channel("test-channel") as channel:
            print("Connected!")
            async for message in channel.messages:
                print(message)


asyncio.run(main())
```

### Notes:

- `REALTIME_URL` is `http://localhost:54321/realtime/v1` when developing locally with the Supabase CLI and `https://<project_ref>.supabase.co/realtime/v1` when connecting to your Supabase project. The client switches to `ws`/`wss` and appends `/websocket` itself.
- The token callback is awaited when connecting and on every heartbeat, so it can return a refreshed user access token. It must return a JWT whose claims contain `exp` and `role` (an existing database role), or the publishable key.
- `async with client.channel(...)` subscribes on entry and unsubscribes on exit. `subscribe()` raises if the server rejects the join.
- Channel name can be any `string`.
- Use `realtime.client.automatically_reconnect(url, get_token, handler)` instead of `connect_once` to reconnect with exponential backoff when the connection drops.

## Broadcast

Your client can send and receive messages based on the `event`.

```python
from realtime import BroadcastMessage, RealtimeChannelOptions

options = RealtimeChannelOptions().broadcast(ack=False, listen_self=False)

async with client.channel("broadcast-test", options) as channel:
    await channel.send_broadcast("some-event", {"hello": "world"})
    async for message in channel.messages:
        if isinstance(message, BroadcastMessage):
            print(message.payload)
```

### Notes:

- With `ack=True`, `send_broadcast()` waits for the server to acknowledge the message and returns its reply.
- With `listen_self=True`, the client receives the broadcast messages it sends.
- `RealtimeChannelOptions().private(True)` makes the server use RLS to decide whether the user may join the channel.
- Setting `replication_ready` to `true` instructs the server to emit a `system` message once the Postgres replication connection backing the channel is established and ready to stream changes. Its payload's `status` is `"ok"` (`message: "Replication connection established"`) on success or `"error"` if the connection is not ready in time.

```python
from realtime import PostgresChangesMessage, RealtimeChannelOptions, SystemMessage

options = (
    RealtimeChannelOptions()
    .broadcast(replication_ready=True)
    .postgres_changes("*", schema="public", table="messages")
)

async with client.channel("db-changes", options) as channel:
    async for message in channel.messages:
        if isinstance(message, SystemMessage) and message.payload.status == "ok":
            print("Replication connection is ready:", message.payload.message)
        elif isinstance(message, PostgresChangesMessage):
            print("Change received!", message.payload)
```

## Presence

Your client can track and sync state that's stored in the channel.

```python
from realtime import RealtimeChannelOptions
from realtime.presence import PresenceJoin, PresenceLeave

options = RealtimeChannelOptions().presence(key="user-1", enabled=True)

async with client.channel("presence-test", options) as channel:
    await channel.track({"user_id": 1})
    async for message in channel.messages:
        if isinstance(message, PresenceJoin):
            print("New users have joined: ", message.new_presences)
        elif isinstance(message, PresenceLeave):
            print("Users have left: ", message.left_presences)
        print("Online users: ", channel.presence_state())
```

## Postgres CDC

Receive database changes on the client.

```python
from realtime import PostgresChangesMessage, RealtimeChannelOptions

options = (
    RealtimeChannelOptions()
    .postgres_changes("*", schema="public")
    .postgres_changes("INSERT", schema="public", table="messages")
    .postgres_changes(
        "UPDATE", schema="public", table="users", filter="username=eq.Realtime"
    )
)

async with client.channel("db-changes", options) as channel:
    print("Ready to receive database changes!")
    async for message in channel.messages:
        if isinstance(message, PostgresChangesMessage):
            print("Change received: ", message.payload)
```

### Filters

`filter` is a `column=operator.value` expression evaluated server-side. The
following operators are supported:

| Operator                | Example                             | Meaning                            |
| ----------------------- | ----------------------------------- | ---------------------------------- |
| `eq`                    | `id=eq.1`                           | equal                              |
| `neq`                   | `id=neq.1`                          | not equal                          |
| `lt` `lte` `gt` `gte`   | `age=gte.18`                        | comparison                         |
| `in`                    | `status=in.(active,pending)`        | in list                            |
| `like` `ilike`          | `title=like.%foo%`                  | pattern match (case in/sensitive)  |
| `is`                    | `deleted_at=is.null`                | `IS null/true/false/unknown`       |
| `match` `imatch`        | `title=match.^foo`                  | POSIX regex match (`~` / `~*`)     |
| `isdistinct`            | `value=isdistinct.1`                | NULL-safe inequality               |

Any operator can be **negated** with the `not.` prefix, e.g.
`filter="status=not.in.(draft,archived)"`. Multiple conditions combined with
commas are applied as an `AND`, e.g.
`filter="amount=gt.100,status=in.(open,pending)"`.

> **Note:** Realtime evaluates filters server-side over a single table's WAL —
> there is no resource embedding or `or()` grouping, and `%` (not `*`) is the
> wildcard for `like`/`ilike`.

### Selecting columns

Use `select` to receive only a subset of columns instead of the full row. This
reduces payload size (helpful for large `bytea`/`jsonb` columns). The selected
columns must be selectable by the subscribing role:

```python
options = RealtimeChannelOptions().postgres_changes(
    "*", schema="public", table="users", select=["id", "first_name"]
)

async with client.channel("db-changes", options) as channel:
    async for message in channel.messages:
        # the record only contains {"id": ..., "first_name": ...}
        print("Selected columns only: ", message)
```

## Get All Channels

You can see all the channels that your client has instantiated.

```python
client.get_channels()
```

## Cleanup

It is highly recommended that you clean up your channels after you're done with them.

- Remove a single channel

```python
channel = client.channel("some-channel-to-remove")
await channel.subscribe()

await client.remove_channel(channel)
```

- Remove all channels

```python
await client.channel("a-channel-to-remove").subscribe()
await client.channel("another-channel-to-remove").subscribe()

await client.remove_all_channels()
```

Leaving `async with client.channel(...)` unsubscribes on its own.

## Credits

This repo draws heavily from [phoenix-js](https://github.com/phoenixframework/phoenix/tree/master/assets/js/phoenix).

## License

MIT.
