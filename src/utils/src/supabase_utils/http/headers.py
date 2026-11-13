from __future__ import annotations

from typing import TYPE_CHECKING

from pyrsistent import PMap, PVector
from pyrsistent import m as Map
from pyrsistent import v as Vec

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, KeysView, Mapping


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

    @staticmethod
    def supabase_client_headers(
        package_name: str, package_version: str, *, features: Iterable[str] = ()
    ) -> Headers:
        """The `X-Client-Info` header that names this SDK, its package and the
        platform it runs on, with a `features` segment listing `features` when
        there are any, see `with_client_info_features()`."""
        from platform import python_version, release, system

        headers = Headers.from_mapping(
            {
                "X-Client-Info": (
                    f"supabase-py/{package_name} v{package_version}"
                    f"; platform={system()}"
                    f"; platform-version={release()}"
                    f"; runtime=python"
                    f"; runtime-version={python_version()}"
                )
            }
        )
        return headers.with_client_info_features(features)

    def with_client_info_features(self, features: Iterable[str]) -> Headers:
        """A copy whose `X-Client-Info` header also lists `features` in its
        `features` segment, as in `...; runtime=python; features=typed-api`.

        The features the header lists already are kept, and the segment is
        rendered once, last, sorted and without duplicates. The headers are
        returned as they are without an `X-Client-Info` header, since the
        segment says what a client used and not which client it is, and
        without `features`.
        """
        merged = set(features)
        if not merged:
            return self
        value = self.get("X-Client-Info")
        if value is None:
            return self
        segments: list[str] = []
        for raw_segment in value.split(";"):
            segment = raw_segment.strip()
            name, separator, listed = segment.partition("=")
            if separator and name.strip().lower() == "features":
                merged.update(
                    feature.strip() for feature in listed.split(",") if feature.strip()
                )
            elif segment:
                segments.append(segment)
        segments.append(f"features={','.join(sorted(merged))}")
        return self.override("X-Client-Info", "; ".join(segments))

    def set(self, key: str, value: str) -> Headers:
        key = key.lower()
        existing: PVector[str] = self._map.get(key, Vec())
        new_values = existing.append(value)
        return Headers(pmap=self._map.set(key, new_values))

    def override(self, key: str, value: str) -> Headers:
        return Headers(pmap=self._map.set(key.lower(), Vec(value)))

    def remove(self, key: str) -> Headers:
        return Headers(pmap=self._map.discard(key.lower()))

    def get(self, key: str) -> str | None:
        if vals := self._map.get(key.lower(), None):
            return ", ".join(vals)
        return None

    def get_list(self, key: str) -> list[str] | None:
        if val := self._map.get(key.lower(), None):
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
        new: PMap[str, PVector[str]] = self._map.update(other._map)
        return Headers(new)

    def iter_items(self) -> list[tuple[str, str]]:
        return [(k, v) for k, vals in self._map.items() for v in vals]

    def __str__(self) -> str:
        fields = ", ".join(f'"{k}"="{self.get(k)}"' for k in self._map)
        return f"Headers({fields})"

    def __repr__(self) -> str:
        return str(self)
