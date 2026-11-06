from __future__ import annotations

from typing import TYPE_CHECKING

from pyrsistent import PMap, PVector
from pyrsistent import m as Map
from pyrsistent import v as Vec

if TYPE_CHECKING:
    from collections.abc import Mapping

    from yarl import Query

QueryValue = str | int | float | bool


class URLQuery:
    def __init__(self, pmap: PMap[str, PVector[QueryValue]]) -> None:
        self._map = pmap

    @staticmethod
    def empty() -> URLQuery:
        return URLQuery(pmap=Map())

    @staticmethod
    def from_mapping(mapping: Mapping[str, QueryValue]) -> URLQuery:
        map: PMap[str, PVector[QueryValue]] = Map()
        for key, val in mapping.items():
            map = map.set(key, Vec(val))
        return URLQuery(pmap=map)

    def set(self, key: str, value: QueryValue) -> URLQuery:
        existing: PVector[QueryValue] = self._map.get(key, Vec())
        new_values = existing.append(value)
        return URLQuery(pmap=self._map.set(key, new_values))

    def get(self, key: str) -> str | None:
        if val := self._map.get(key, None):
            return "&".join(str(v) for v in val)
        return None

    def get_list(self, key: str) -> list[QueryValue] | None:
        if val := self._map.get(key, None):
            return list(val)
        return None

    def __contains__(self, key: str) -> bool:
        return key in self._map

    def __getitem__(self, key: str) -> str:
        if val := self.get(key):
            return val
        raise KeyError(f"'{key}' not found.")

    def as_query(self) -> Query:
        return {key: list(vals) for key, vals in self._map.items()}

    def merge(self, other: URLQuery) -> URLQuery:
        new: PMap[str, PVector[QueryValue]] = self._map.update(other._map)
        return URLQuery(new)

    def __len__(self) -> int:
        return len(self._map)

    def __repr__(self) -> str:
        fields = ", ".join(f'"{k}"="{self.get_list(k)}"' for k in self._map)
        return f"URLQuery({fields})"
