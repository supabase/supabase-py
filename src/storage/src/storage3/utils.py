from deprecation import deprecated
from httpx import AsyncClient as AsyncClient  # noqa: F401
from httpx import Client

from .version import __version__


class SyncClient(Client):
    @deprecated(
        "0.11.3", "1.0.0", __version__, "Use `Client` from the httpx package instead"
    )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @deprecated(
        "0.11.3",
        "1.0.0",
        __version__,
        "Use `close` method from `Client` in the httpx package instead",
    )
    def aclose(self) -> None:
        self.close()


class StorageException(Exception):
    """Error raised when an operation on the storage API fails."""
