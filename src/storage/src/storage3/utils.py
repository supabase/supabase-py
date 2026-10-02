from typing import Any, Mapping, Optional

from deprecation import deprecated
from httpx import AsyncClient as AsyncClient  # noqa: F401
from httpx import Client

from .constants import DEFAULT_FILE_OPTIONS
from .version import __version__


def merge_file_options(
    file_options: Optional[Mapping[str, Any]],
) -> dict[str, Any]:
    options: dict[str, Any] = {**DEFAULT_FILE_OPTIONS}
    for key, value in (file_options or {}).items():
        normalized_key = "content-type" if key.lower() == "content-type" else key
        options[normalized_key] = value
    return options


class SyncClient(Client):
    @deprecated(
        "0.11.3", "3.0.0", __version__, "Use `Client` from the httpx package instead"
    )
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    @deprecated(
        "0.11.3",
        "3.0.0",
        __version__,
        "Use `close` method from `Client` in the httpx package instead",
    )
    def aclose(self) -> None:
        self.close()


class StorageException(Exception):
    """Error raised when an operation on the storage API fails."""
