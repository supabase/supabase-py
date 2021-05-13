from typing import Any, Dict

import requests
from httpx import AsyncClient
from postgrest_py.client import PostgrestClient
from postgrest_py.request_builder import QueryRequestBuilder

from .realtime_client import SupabaseRealtimeClient


def _execute_monkey_patch(self) -> Dict[str, Any]:
    """Temporary method to enable syncronous client code."""
    method: str = self.http_method.lower()
    additional_kwargs: Dict[str, Any] = {}
    if method == "get":
        func = requests.get
    elif method == "post":
        func = requests.post
        # Additionally requires the json body (e.g on insert, self.json==row).
        additional_kwargs = {"json": self.json}
    elif method == "put":
        func = requests.put
    elif method == "patch":
        func = requests.patch
    elif method == "delete":
        func = requests.delete
    else:
        raise NotImplementedError(f"Method '{method}' not recognised.")
    url: str = str(self.session.base_url).rstrip("/")
    query: str = str(self.session.params)
    response = func(f"{url}?{query}", headers=self.session.headers, **additional_kwargs)
    return {
        "data": response.json(),
        "status_code": response.status_code,
    }


# NOTE(fedden): Here we monkey patch the otherwise async method and use the
#               requests module instead. Hopefully cleans things up a little
#               for the user as they are now not bound to async methods.
QueryRequestBuilder.execute = _execute_monkey_patch


class SupabaseQueryBuilder(PostgrestClient):
    def __init__(self, url, headers, schema, realtime, table):
        """
        Subscribe to realtime changes in your database.

        Parameters
        ----------
        url
            Base URL of the Supabase Instance that the client library is acting on
        headers
            authentication/authorization headers which are passed in.
        schema
            schema of table that we are building queries for
        realtime
            realtime-py client
        table
            Name of table to look out for operations on
        Returns
        -------
        None
        """
        super().__init__(base_url=url)
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Accept-Profile": schema,
            "Content-Profile": schema,
            **headers,
        }
        self.session = AsyncClient(base_url=url, headers=headers)
        # self._subscription = SupabaseRealtimeClient(realtime, schema, table)
        # self._realtime = realtime

    def on(self, event, callback):
        """Subscribe to realtime changes in your database.

        Parameters
        ----------
        event
            the event which we are looking out for.
        callback
            function to be execute when the event is received

        Returns
        -------
        SupabaseRealtimeClient
        Returns an instance of a SupabaseRealtimeClient to allow for chaining.
        """
        if not self._realtime.connected:
            self._realtime.connect()
        return self._subscription.on(event, callback)
