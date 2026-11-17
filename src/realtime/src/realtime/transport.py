from collections.abc import Awaitable, Callable
from typing import Protocol


class WebSocketConnection(Protocol):
    """
    An open WebSocket connection, as returned by a `WebSocketTransport`.

    A ``websockets`` client connection already satisfies it. Once the
    connection is closed, `send` and `recv` must raise, preferably a
    ``websockets.ConnectionClosed`` or an `OSError` such as `ConnectionError`.
    """

    async def send(self, message: str | bytes, /) -> None:
        """Send a text frame for a `str` and a binary frame for `bytes`."""
        ...

    async def recv(self) -> str | bytes:
        """Wait for the next frame: `str` for a text frame, `bytes` for a binary one."""
        ...

    async def close(self) -> None:
        """Close the connection. Closing it again must do nothing."""
        ...


type WebSocketTransport = Callable[[str], Awaitable[WebSocketConnection]]
"""
Opens a WebSocket connection to the given URL, which carries the API key and
the protocol version in its query string. An error it raises fails the
connect, and the client retries it like any other failed reconnect.
"""
