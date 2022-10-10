import re
from typing import Any, Dict, Union

from httpx import Timeout
from postgrest import SyncFilterRequestBuilder, SyncPostgrestClient, SyncRequestBuilder
from postgrest.constants import DEFAULT_POSTGREST_CLIENT_TIMEOUT
from supafunc import FunctionsClient

from .lib.auth_client import SupabaseAuthClient
from .lib.client_options import ClientOptions
from .lib.storage_client import SupabaseStorageClient


class Client:
    """Supabase client class."""

    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        options: ClientOptions = ClientOptions(),
    ):
        """Instantiate the client.

        Parameters
        ----------
        supabase_url: str
            The URL to the Supabase instance that should be connected to.
        supabase_key: str
            The API key to the Supabase instance that should be connected to.
        **options
            Any extra settings to be optionally specified - also see the
            `DEFAULT_OPTIONS` dict.
        """

        if not supabase_url:
            raise Exception("supabase_url is required")
        if not supabase_key:
            raise Exception("supabase_key is required")
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        options.headers.update(self._get_auth_headers())
        self.rest_url: str = f"{supabase_url}/rest/v1"
        self.realtime_url: str = f"{supabase_url}/realtime/v1".replace("http", "ws")
        self.auth_url: str = f"{supabase_url}/auth/v1"
        self.storage_url = f"{supabase_url}/storage/v1"
        is_platform = re.search(r"(supabase\.co)|(supabase\.in)", supabase_url)
        if is_platform:
            url_parts = supabase_url.split(".")
            self.functions_url = (
                f"{url_parts[0]}.functions.{url_parts[1]}.{url_parts[2]}"
            )

        else:
            self.functions_url = f"{supabase_url}/functions/v1"
        self.schema: str = options.schema

        # Instantiate clients.
        self.auth = self._init_supabase_auth_client(
            auth_url=self.auth_url,
            supabase_key=self.supabase_key,
            client_options=options,
        )
        # TODO(fedden): Bring up to parity with JS client.
        # self.realtime: SupabaseRealtimeClient = self._init_realtime_client(
        #     realtime_url=self.realtime_url,
        #     supabase_key=self.supabase_key,
        # )
        self.realtime = None
        self.postgrest = self._init_postgrest_client(
            rest_url=self.rest_url,
            supabase_key=self.supabase_key,
            headers=options.headers,
            schema=options.schema,
        )

    def functions(self) -> FunctionsClient:
        return FunctionsClient(self.functions_url, self._get_auth_headers())

    def storage(self) -> SupabaseStorageClient:
        """Create instance of the storage client"""
        return SupabaseStorageClient(self.storage_url, self._get_auth_headers())

    def table(self, table_name: str) -> SyncRequestBuilder:
        """Perform a table operation.

        Note that the supabase client uses the `from` method, but in Python,
        this is a reserved keyword so we have elected to use the name `table`.
        Alternatively you can use the `.from_()` method.
        """
        return self.from_(table_name)

    def from_(self, table_name: str) -> SyncRequestBuilder:
        """Perform a table operation.

        See the `table` method.
        """
        return self.postgrest.from_(table_name)

    def rpc(self, fn: str, params: Dict[Any, Any]) -> SyncFilterRequestBuilder:
        """Performs a stored procedure call.

        Parameters
        ----------
        fn : callable
            The stored procedure call to be executed.
        params : dict of any
            Parameters passed into the stored procedure call.

        Returns
        -------
        SyncFilterRequestBuilder
            Returns a filter builder. This lets you apply filters on the response
            of an RPC.
        """
        return self.postgrest.rpc(fn, params)

    #     async def remove_subscription_helper(resolve):
    #         try:
    #             await self._close_subscription(subscription)
    #             open_subscriptions = len(self.get_subscriptions())
    #             if not open_subscriptions:
    #                 error = await self.realtime.disconnect()
    #                 if error:
    #                     return {"error": None, "data": { open_subscriptions}}
    #         except Exception as e:
    #             raise e
    #     return remove_subscription_helper(subscription)

    # async def _close_subscription(self, subscription):
    #    """Close a given subscription

    #    Parameters
    #    ----------
    #    subscription
    #        The name of the channel
    #    """
    #    if not subscription.closed:
    #        await self._closeChannel(subscription)

    # def get_subscriptions(self):
    #     """Return all channels the client is subscribed to."""
    #     return self.realtime.channels

    # @staticmethod
    # def _init_realtime_client(
    #     realtime_url: str, supabase_key: str
    # ) -> SupabaseRealtimeClient:
    #     """Private method for creating an instance of the realtime-py client."""
    #     return SupabaseRealtimeClient(
    #         realtime_url, {"params": {"apikey": supabase_key}}
    #     )

    @staticmethod
    def _init_supabase_auth_client(
        auth_url: str,
        supabase_key: str,
        client_options: ClientOptions,
    ) -> SupabaseAuthClient:
        """Creates a wrapped instance of the GoTrue Client."""
        return SupabaseAuthClient(
            url=auth_url,
            auto_refresh_token=client_options.auto_refresh_token,
            persist_session=client_options.persist_session,
            local_storage=client_options.local_storage,
            headers=client_options.headers,
        )

    @staticmethod
    def _init_postgrest_client(
        rest_url: str,
        supabase_key: str,
        headers: Dict[str, str],
        schema: str,
        timeout: Union[int, float, Timeout] = DEFAULT_POSTGREST_CLIENT_TIMEOUT,
    ) -> SyncPostgrestClient:
        """Private helper for creating an instance of the Postgrest client."""
        client = SyncPostgrestClient(
            rest_url, headers=headers, schema=schema, timeout=timeout
        )
        client.auth(token=supabase_key)
        return client

    def _get_auth_headers(self) -> Dict[str, str]:
        """Helper method to get auth headers."""
        # What's the corresponding method to get the token
        return {
            "apiKey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
        }


def create_client(
    supabase_url: str,
    supabase_key: str,
    options: ClientOptions = ClientOptions(),
) -> Client:
    """Create client function to instantiate supabase client like JS runtime.

    Parameters
    ----------
    supabase_url: str
        The URL to the Supabase instance that should be connected to.
    supabase_key: str
        The API key to the Supabase instance that should be connected to.
    **options
        Any extra settings to be optionally specified - also see the
        `DEFAULT_OPTIONS` dict.

    Examples
    --------
    Instantiating the client.
    >>> import os
    >>> from supabase import create_client, Client
    >>>
    >>> url: str = os.environ.get("SUPABASE_TEST_URL")
    >>> key: str = os.environ.get("SUPABASE_TEST_KEY")
    >>> supabase: Client = create_client(url, key)

    Returns
    -------
    Client
    """
    return Client(supabase_url=supabase_url, supabase_key=supabase_key, options=options)
