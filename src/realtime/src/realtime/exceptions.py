from supabase_utils.errors import SupabaseError
from supabase_utils.http.errors import SupabaseAPIError

_AUTHORIZATION_ERROR_CODES = frozenset(
    {
        "InvalidJWTToken",
        "JwtSignatureError",
        "JwtSignerError",
        "MalformedJWT",
        "Unauthorized",
    }
)
_FATAL_JOIN_ERROR_CODES = frozenset(
    {
        "PrivateOnly",
        "RealtimeDisabledForTenant",
        "TenantNotFound",
        "TopicNameRequired",
        "UnableToReplayMessages",
    }
)


class RealtimeError(SupabaseError):
    """Raised when a realtime operation fails."""


class NotConnectedError(RealtimeError):
    """
    Raised when an operation needs a connection that is not established, or
    that dropped before the server replied.
    """

    def __init__(self, func_name: str, message: str | None = None) -> None:
        super().__init__(
            message
            or "A WebSocket connection has not been established. Subscribe to a "
            "channel or call RealtimeClient.connect() before calling "
            f"{func_name}()"
        )
        self.offending_func_name: str = func_name


class RealtimeTimeoutError(RealtimeError, TimeoutError):
    """Raised when the server does not reply to a push within the timeout."""

    def __init__(self, event: str, topic: str, timeout: float) -> None:
        super().__init__(
            f"the server did not reply to {event} on {topic!r} within {timeout} seconds"
        )
        self.event = event
        self.topic = topic
        self.timeout = timeout


class ChannelNotJoinedError(RealtimeError):
    """
    Raised when an operation needs a joined channel and the channel is not
    joined: before `subscribe()` completes, after `unsubscribe()`, or while
    the client joins it again after a reconnect. Nothing was sent.
    """

    def __init__(self, func_name: str, topic: str) -> None:
        super().__init__(
            f"{func_name}() needs the channel {topic!r} to be joined; nothing was sent"
        )
        self.offending_func_name: str = func_name
        self.topic = topic


class PushRejectedError(RealtimeError):
    """
    Raised when the server replies to a push with an error.

    `reason` is the reason the server gave, or ``None`` when it gave none.
    `code` is the error code the server gave, such as
    ``persistence_unauthorized``, or ``None`` when it gave none.
    """

    def __init__(
        self,
        event: str,
        topic: str,
        reason: str | None,
        *,
        code: str | None = None,
    ) -> None:
        detail = reason or code
        super().__init__(
            f"the server rejected {event} on {topic!r}"
            + (f": {detail}" if detail else ""),
            code=code,
        )
        self.event = event
        self.topic = topic
        self.reason = reason


class RealtimeAPIError(RealtimeError, SupabaseAPIError):
    """
    Raised when the Realtime REST API answers a request with an error, such as
    `RealtimeChannel.http_send()` with a status other than 202.
    """


class ChannelClosedError(RealtimeError):
    """
    Raised when the channel closes or errors while a call waits for the
    server's reply.

    `reason` is the message of the ``system`` error the server sent before it
    closed the channel, such as ``Client presence rate limit exceeded``, or
    ``None`` when it sent none.
    """

    def __init__(self, topic: str, reason: str | None) -> None:
        super().__init__(
            f"the channel {topic!r} closed before the server replied"
            + (f": {reason}" if reason else "")
        )
        self.topic = topic
        self.reason = reason


class ChannelJoinError(RealtimeError):
    """
    Raised when the server rejects the join of a channel.

    `reason` is the reason the server gave, and `code` its prefix, such as
    `ChannelRateLimitReached`, when the reason has one.
    """

    def __init__(self, topic: str, reason: str) -> None:
        prefix, separator, _ = reason.partition(":")
        super().__init__(
            f"the server rejected the join of {topic!r}: {reason}",
            code=prefix if separator and " " not in prefix else None,
        )
        self.topic = topic
        self.reason = reason


class AuthorizationError(ChannelJoinError):
    """
    Raised when the server rejects the access token of a join, or when the
    row level security policies deny the join of a private channel.
    """


def _join_error(topic: str, reason: str) -> ChannelJoinError:
    error = ChannelJoinError(topic, reason)
    if error.code in _AUTHORIZATION_ERROR_CODES:
        return AuthorizationError(topic, reason)
    return error


def _is_fatal(error: Exception) -> bool:
    if isinstance(error, AuthorizationError):
        return True
    if isinstance(error, ChannelJoinError):
        return error.code in _FATAL_JOIN_ERROR_CODES
    return isinstance(error, RealtimeError) and not isinstance(
        error, (NotConnectedError, RealtimeTimeoutError)
    )
