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

## Creating a Channel

```python
import asyncio
from typing import Optional

from realtime import AsyncRealtimeClient, RealtimeSubscribeStates


async def main():
    REALTIME_URL = "ws://localhost:4000/websocket"
    API_KEY = "1234567890"

    socket = AsyncRealtimeClient(REALTIME_URL, API_KEY)
    channel = socket.channel("test-channel")

    def _on_subscribe(status: RealtimeSubscribeStates, err: Optional[Exception]):
        if status == RealtimeSubscribeStates.SUBSCRIBED:
            print("Connected!")
        elif status == RealtimeSubscribeStates.CHANNEL_ERROR:
            print(f"There was an error subscribing to channel: {err.args}")
        elif status == RealtimeSubscribeStates.TIMED_OUT:
            print("Realtime server did not respond in time.")
        elif status == RealtimeSubscribeStates.CLOSED:
            print("Realtime channel was unexpectedly closed.")

    await channel.subscribe(_on_subscribe)
```

### Notes:

- `REALTIME_URL` is `ws://localhost:4000/socket` when developing locally and `wss://<project_ref>.supabase.co/realtime/v1` when connecting to your Supabase project.
- `API_KEY` is a JWT whose claims must contain `exp` and `role` (existing database role).
- Channel name can be any `string`.

## Broadcast

Your client can send and receive messages based on the `event`.

```python
# Setup...

channel = client.channel(
    "broadcast-test", {"config": {"broadcast": {"ack": False, "self": False}}}
)

await channel.on_broadcast("some-event", lambda payload: print(payload)).subscribe()
await channel.send_broadcast("some-event", {"hello": "world"})
```

### Notes:

- Setting `ack` to `true` means that the `channel.send` promise will resolve once server replies with acknowledgement that it received the broadcast message request.
- Setting `self` to `true` means that the client will receive the broadcast message it sent out.
- Setting `private` to `true` means that the client will use RLS to determine if the user can connect or not to a given channel.

## Presence

Your client can track and sync state that's stored in the channel.

```python
# Setup...

channel = client.channel(
    "presence-test",
    {
        "config": {
            "presence": {
                "key": ""
            }
        }
    }
)

channel.on_presence_sync(lambda: print("Online users: ", channel.presence_state()))
channel.on_presence_join(lambda new_presences: print("New users have joined: ", new_presences))
channel.on_presence_leave(lambda left_presences: print("Users have left: ", left_presences))

await channel.track({ 'user_id': 1 })
```

## Postgres CDC

Receive database changes on the client.

```python
# Setup...

channel = client.channel("db-changes")

channel.on_postgres_changes(
    "*",
    schema="public",
    callback=lambda payload: print("All changes in public schema: ", payload),
)

channel.on_postgres_changes(
    "INSERT",
    schema="public",
    table="messages",
    callback=lambda payload: print("All inserts in messages table: ", payload),
)

channel.on_postgres_changes(
    "UPDATE",
    schema="public",
    table="users",
    filter="username=eq.Realtime",
    callback=lambda payload: print(
        "All updates on users table when username is Realtime: ", payload
    ),
)

channel.subscribe(
    lambda status, err: status == RealtimeSubscribeStates.SUBSCRIBED
    and print("Ready to receive database changes!")
)
```

## Get All Channels

You can see all the channels that your client has instantiated.

```python
# Setup...

client.get_channels()
```

## Cleanup

It is highly recommended that you clean up your channels after you're done with them.

- Remove a single channel

```python
# Setup...

channel = client.channel('some-channel-to-remove')

channel.subscribe()

await client.remove_channel(channel)
```

- Remove all channels

```python
# Setup...

channel1 = client.channel('a-channel-to-remove')
channel2 = client.channel('another-channel-to-remove')

await channel1.subscribe()
await channel2.subscribe()

await client.remove_all_channels()
```

## Credits

This repo draws heavily from [phoenix-js](https://github.com/phoenixframework/phoenix/tree/master/assets/js/phoenix).

## License

MIT.
