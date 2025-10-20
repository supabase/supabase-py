from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Optional, Union

from httpx import AsyncClient, BasicAuth, Client, Headers, Timeout
from yarl import URL

from .utils import is_http_url


class BasePostgrestClient(ABC):
    """Base PostgREST client."""

    def __init__(
        self,
        base_url: URL,
        *,
        schema: str,
        headers: Dict[str, str],
        timeout: Union[int, float, Timeout],
        verify: bool = True,
        proxy: Optional[str] = None,
    ) -> None:
        if not is_http_url(base_url):
            ValueError("base_url must be a valid HTTP URL string")

        self.base_url = base_url
        self.headers = Headers(headers)
        self.headers["Accept-Profile"] = schema
        self.headers["Content-Profile"] = schema
        self.timeout = timeout
        self.verify = verify
        self.proxy = proxy
        self.basic_auth: BasicAuth | None = None

    def auth(
        self,
        token: Optional[str],
        *,
        username: Union[str, bytes, None] = None,
        password: Union[str, bytes] = "",
    ):
        """
        Authenticate the client with either bearer token or basic authentication.

        Raises:
            `ValueError`: If neither authentication scheme is provided.

        .. note::
            Bearer token is preferred if both ones are provided.
        """
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
        elif username:
            self.basic_auth = BasicAuth(username, password)
        else:
            raise ValueError(
                "Neither bearer token or basic authentication scheme is provided"
            )
        return self
