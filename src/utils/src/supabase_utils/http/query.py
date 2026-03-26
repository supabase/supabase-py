from __future__ import annotations

from typing import Mapping

from pyrsistent import PMap, PVector
from pyrsistent import m as Map
from pyrsistent import v as Vec
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
            map = map.set(key.lower(), Vec(val))
        return URLQuery(pmap=map)

    def set(self, key: str, val: QueryValue) -> URLQuery:
        existing: PVector[QueryValue] = self._map.get(key, Vec())
        new_val = existing.append(val)
        return URLQuery(pmap=self._map.set(key, new_val))

    def get(self, key: str) -> list[QueryValue] | None:
        if val := self._map.get(key, None):
            return list(val)
        return None

    def __contains__(self, key: str) -> bool:
        return key in self._map

    def as_query(self) -> Query:
        return {key: list(vals) for key, vals in self._map.items()}

    def merge(self, other: URLQuery) -> URLQuery:
        new = self._map.update(other._map)
        return URLQuery(new)

    def __str__(self) -> str:
        fields = ", ".join(f'"{k}"="{self.get(k)}"' for k in self._map)
        return f"URLQuery({fields})"

    def __repr__(self) -> str:
        return str(self)
