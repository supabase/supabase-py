from dataclasses import dataclass

from realtime.transport import WebSocketTransport
from realtime.types import (
    DEFAULT_HEARTBEAT_INTERVAL,
    DEFAULT_HEARTBEAT_TIMEOUT,
    DEFAULT_MAX_QUEUED_MESSAGES,
    DEFAULT_TIMEOUT,
    validate_disconnect_delay,
    validate_heartbeat,
    validate_push_options,
)
from supabase_auth import AsyncSupportedStorage, AuthFlowType, SyncSupportedStorage
from supabase_auth.constants import STORAGE_KEY
from supabase_utils.http.request import validate_request_timeout
from supabase_utils.http.retry import RetryPolicy


@dataclass(frozen=True)
class RealtimeClientOptions:
    """Options for the realtime connections opened by `AsyncClient.realtime`."""

    heartbeat_interval: float = DEFAULT_HEARTBEAT_INTERVAL
    """Seconds between heartbeats. Must be positive."""

    heartbeat_timeout: float = DEFAULT_HEARTBEAT_TIMEOUT
    """Seconds to wait for a heartbeat reply before the connection is considered lost. Must be positive."""

    timeout: float = DEFAULT_TIMEOUT
    """Seconds to wait for the server to reply to a join, a leave, a presence update or an acknowledged broadcast. Must be positive."""

    max_queued_messages: int = DEFAULT_MAX_QUEUED_MESSAGES
    """Messages each channel keeps until they are read from `RealtimeChannel.messages`. When a channel's queue is full, its oldest message is dropped and a warning is logged. Must be positive."""

    transport: WebSocketTransport | None = None
    """Opens the WebSocket connection, instead of the ``websockets`` library."""

    disconnect_on_empty_channels_after: float | None = None
    """Seconds to keep the connection open after the last channel is removed. Defaults to twice ``heartbeat_interval``, and ``0`` disconnects at once. Must not be negative."""

    def __post_init__(self) -> None:
        validate_heartbeat(self.heartbeat_interval, self.heartbeat_timeout)
        validate_push_options(self.timeout, self.max_queued_messages)
        if self.disconnect_on_empty_channels_after is not None:
            validate_disconnect_delay(self.disconnect_on_empty_channels_after)


@dataclass(frozen=True, kw_only=True)
class _ServiceClientOptions:
    """Options shared by the database, auth, storage and edge functions clients."""

    request_timeout: float | None = None
    """Seconds a request to the service may go without progress before it fails with `RequestTimeoutError`. Overrides the `request_timeout` argument of the client when set."""

    retry: RetryPolicy | None = None
    """How requests to the service that failed in a way worth repeating are retried. Overrides the `retry` argument of the client when set."""

    def __post_init__(self) -> None:
        validate_request_timeout(self.request_timeout)


@dataclass(frozen=True, kw_only=True)
class PostgrestClientOptions(_ServiceClientOptions):
    """Options for the database client. Use `request_timeout()` and `retry()` on a query to override its timeout and retries for that query."""

    schema: str = "public"
    """The Postgres schema which your tables belong to. Must be on the list of exposed schemas in Supabase."""


@dataclass(frozen=True, kw_only=True)
class AuthClientOptions[Storage: (AsyncSupportedStorage, SyncSupportedStorage)](
    _ServiceClientOptions
):
    """Options for the auth client.

    `AsyncClient` takes an `AsyncSupportedStorage` as `session_storage` and
    `Client` a `SyncSupportedStorage`.
    """

    auto_refresh_token: bool = True
    """Automatically refreshes the token for logged in users."""

    session_storage: Storage | None = None
    """Where the logged in session is stored. None (the default) keeps it in memory."""

    storage_key: str = STORAGE_KEY
    """The key the session is stored under in `session_storage`. Give clients that share a `session_storage` different keys so they do not overwrite each other's session."""

    flow_type: AuthFlowType = "pkce"
    """The flow type to use for authentication."""

    append_flow_id_to_redirects: bool = False
    """Adds the id of each PKCE flow to the redirect URL it is given, such as `redirect_to` or `email_redirect_to`, as the `sb_flow_id` query parameter, for the callback to pass to `exchange_code_for_session(code, flow_id=...)`. That way the callback completes the flow that sent the user there, even when several flows are pending, including flows that are completed from an email link. Allow the parameter in the redirect URL allow list first: an entry without a wildcard no longer matches the URL, and the auth service then redirects to the Site URL instead."""


@dataclass(frozen=True, kw_only=True)
class StorageClientOptions(_ServiceClientOptions):
    """Options for the storage client. The default `RetryPolicy` retries GET and HEAD requests only, so an upload is not retried unless `retry` lists its method."""


@dataclass(frozen=True, kw_only=True)
class FunctionsClientOptions(_ServiceClientOptions):
    """Options for the edge functions client. Use the `request_timeout` and `retry` arguments of `invoke()` to override its timeout and retries for one invocation."""
