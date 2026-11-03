from __future__ import annotations

from abc import ABC, abstractmethod


class AsyncSupportedStorage(ABC):
    @abstractmethod
    async def get_item(self, key: str) -> str | None: ...  # pragma: no cover

    @abstractmethod
    async def set_item(self, key: str, value: str) -> None: ...  # pragma: no cover

    @abstractmethod
    async def remove_item(self, key: str) -> None: ...  # pragma: no cover


class AsyncMemoryStorage(AsyncSupportedStorage):
    def __init__(self) -> None:
        self.storage: dict[str, str] = {}

    async def get_item(self, key: str) -> str | None:
        if key in self.storage:
            return self.storage[key]
        return None

    async def set_item(self, key: str, value: str) -> None:
        self.storage[key] = value

    async def remove_item(self, key: str) -> None:
        if key in self.storage:
            del self.storage[key]
