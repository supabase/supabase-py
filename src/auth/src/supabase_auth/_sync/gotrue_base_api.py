from __future__ import annotations

from typing import Any, Callable, Dict, Optional, TypeVar, overload

from httpx import Response
from pydantic import BaseModel
from typing_extensions import Literal, Self

from ..constants import API_VERSION_HEADER_NAME, API_VERSIONS
from ..helpers import handle_exception, model_dump
from ..http_clients import SyncClient

T = TypeVar("T")


class SyncGoTrueBaseAPI:
    def __init__(
        self,
        *,
        url: str,
        headers: Dict[str, str],
        http_client: Optional[SyncClient],
        verify: bool = True,
        proxy: Optional[str] = None,
    ):
        self._url = url
        self._headers = headers
        self._http_client = http_client or SyncClient(
            verify=bool(verify),
            proxy=proxy,
            follow_redirects=True,
            http2=True,
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_t, exc_v, exc_tb) -> None:
        self.close()

    def close(self) -> None:
        self._http_client.aclose()

    @overload
    def _request(
        self,
        method: Literal["GET", "OPTIONS", "HEAD", "POST", "PUT", "PATCH", "DELETE"],
        path: str,
        *,
        jwt: Optional[str] = None,
        redirect_to: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        query: Optional[Dict[str, str]] = None,
        body: Optional[Any] = None,
        no_resolve_json: Literal[False] = False,
        xform: Callable[[Any], T],
    ) -> T: ...  # pragma: no cover

    @overload
    def _request(
        self,
        method: Literal["GET", "OPTIONS", "HEAD", "POST", "PUT", "PATCH", "DELETE"],
        path: str,
        *,
        jwt: Optional[str] = None,
        redirect_to: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        query: Optional[Dict[str, str]] = None,
        body: Optional[Any] = None,
        no_resolve_json: Literal[True],
        xform: Callable[[Response], T],
    ) -> T: ...  # pragma: no cover

    @overload
    def _request(
        self,
        method: Literal["GET", "OPTIONS", "HEAD", "POST", "PUT", "PATCH", "DELETE"],
        path: str,
        *,
        jwt: Optional[str] = None,
        redirect_to: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        query: Optional[Dict[str, str]] = None,
        body: Optional[Any] = None,
        no_resolve_json: bool = False,
    ) -> None: ...  # pragma: no cover

    def _request(
        self,
        method: Literal["GET", "OPTIONS", "HEAD", "POST", "PUT", "PATCH", "DELETE"],
        path: str,
        *,
        jwt: Optional[str] = None,
        redirect_to: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        query: Optional[Dict[str, str]] = None,
        body: Optional[Any] = None,
        no_resolve_json: bool = False,
        xform: Optional[Callable[[Any], T]] = None,
    ) -> Optional[T]:
        url = f"{self._url}/{path}"
        headers = {**self._headers, **(headers or {})}
        if API_VERSION_HEADER_NAME not in headers:
            headers[API_VERSION_HEADER_NAME] = API_VERSIONS["2024-01-01"].get("name")
        if "Content-Type" not in headers:
            headers["Content-Type"] = "application/json;charset=UTF-8"
        if jwt:
            headers["Authorization"] = f"Bearer {jwt}"
        query = query or {}
        if redirect_to:
            query["redirect_to"] = redirect_to
        try:
            response = self._http_client.request(
                method,
                url,
                headers=headers,
                params=query,
                json=model_dump(body) if isinstance(body, BaseModel) else body,
            )
            response.raise_for_status()
            result = response if no_resolve_json else response.json()
            if xform:
                return xform(result)
        except Exception as e:
            raise handle_exception(e)
