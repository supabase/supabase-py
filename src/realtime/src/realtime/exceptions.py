from supabase_utils.errors import SupabaseError


class RealtimeError(SupabaseError):
    """Raised when a realtime operation fails."""


class NotConnectedError(RealtimeError):
    """
    Raised when operations requiring a connection are executed when socket is not connected
    """

    def __init__(self, func_name: str) -> None:
        super().__init__(
            "A WebSocket connection has not been established. Subscribe to a "
            "channel or call RealtimeClient.connect() before calling "
            f"{func_name}()"
        )
        self.offending_func_name: str = func_name


class AuthorizationError(RealtimeError):
    """
    Raised when there is an authorization failure for private channels
    """

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or "Authorization failed for private channel")


class MaxRetriesExceeded(RealtimeError):
    """Raised when reconnecting failed `retries` times in a row."""

    def __init__(self, retries: int) -> None:
        super().__init__(f"Reconnecting failed after {retries} attempts")
        self.retries = retries
