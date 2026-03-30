from __future__ import annotations

from typing import Iterator, KeysView, Mapping

from pyrsistent import PMap, PVector
from pyrsistent import m as Map
from pyrsistent import v as Vec


class Headers:
    def __init__(self, pmap: PMap[str, PVector[str]]) -> None:
        self._map = pmap

    @staticmethod
    def empty() -> Headers:
        return Headers(pmap=Map())

    @staticmethod
    def from_mapping(mapping: Mapping[str, str]) -> Headers:
        map: PMap[str, PVector[str]] = Map()
        for key, val in mapping.items():
            map = map.set(key.lower(), Vec(val))
        return Headers(pmap=map)

    def set(self, key: str, val: str) -> Headers:
        key = key.lower()
        existing: PVector[str] = self._map.get(key, Vec())
        new_val = existing.append(val)
        return Headers(pmap=self._map.set(key, new_val))

    def override(self, key: str, val: str) -> Headers:
        return Headers(pmap=self._map.set(key.lower(), Vec(val)))

    def get(self, key: str) -> str | None:
        if vals := self._map.get(key.lower(), None):
            return ", ".join(vals)
        return None

    def get_list(self, key: str) -> list[str] | None:
        if val := self._map.get(key, None):
            return list(val)
        return None

    def __getitem__(self, key: str) -> str:
        if val := self.get(key):
            return val
        raise KeyError(f"'{key}' not found.")

    def __len__(self) -> int:
        return len(self._map)

    def __contains__(self, key: str) -> bool:
        return key.lower() in self._map

    def keys(self) -> KeysView[str]:
        return self._map.keys()

    def __iter__(self) -> Iterator[str]:
        return iter(self.keys())

    def update(self, other: Headers) -> Headers:
        new = self._map.update(other._map)
        return Headers(new)

    def iter_items(self) -> list[tuple[str, str]]:
        return [(k, v) for k, vals in self._map.items() for v in vals]

    def __str__(self) -> str:
        fields = ", ".join(f'"{k}"="{self.get(k)}"' for k in self._map)
        return f"Headers({fields})"

    def __repr__(self) -> str:
        return str(self)
