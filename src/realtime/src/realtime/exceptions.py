from typing import Optional


class NotConnectedError(Exception):
    """
    Raised when operations requiring a connection are executed when socket is not connected
    """

    def __init__(self, func_name: str):
        self.offending_func_name: str = func_name

    def __str__(self):
        return f"A WS connection has not been established. Ensure you call AsyncRealtimeClient.connect() before calling AsyncRealtimeClient.{self.offending_func_name}()"


class AuthorizationError(Exception):
    """
    Raised when there is an authorization failure for private channels
    """

    def __init__(self, message: Optional[str] = None):
        self.message: str = message or "Authorization failed for private channel"

    def __str__(self):
        return self.message
