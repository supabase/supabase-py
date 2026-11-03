class NotConnectedError(Exception):
    """
    Raised when operations requiring a connection are executed when socket is not connected
    """

    def __init__(self, func_name: str) -> None:
        self.offending_func_name: str = func_name

    def __str__(self) -> str:
        return f"A WS connection has not been established. Ensure you call AsyncRealtimeClient.connect() before calling AsyncRealtimeClient.{self.offending_func_name}()"


class AuthorizationError(Exception):
    """
    Raised when there is an authorization failure for private channels
    """

    def __init__(self, message: str | None = None) -> None:
        self.message: str = message or "Authorization failed for private channel"

    def __str__(self) -> str:
        return self.message


class RealtimeHTTPError(Exception):
    """
    Raised when a request to the Realtime REST API fails, e.g. `AsyncRealtimeChannel.http_send`.

    `status` is the HTTP status code, or None when no response was received (timeout).
    """

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.message: str = message
        self.status: int | None = status

    def __str__(self) -> str:
        return self.message
