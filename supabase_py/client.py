from postgrest_py import PostgrestClient
from supabase_py.lib.auth_client import SupabaseAuthClient
from supabase_py.lib.realtime_client import SupabaseRealtimeClient
from supabase_py.lib.query_builder import SupabaseQueryBuilder

from typing import Any, Dict


DEFAULT_OPTIONS = {
    "schema": "public",
    "auto_refresh_token": True,
    "persist_session": True,
    "detect_session_in_url": True,
    "local_storage": {},
}


class Client:
    """Supabase client class."""

    def __init__(
        self, supabase_url: str, supabase_key: str, **options,
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
        # Start with defaults, write headers and prioritise user overwrites.
        settings: Dict[str, Any] = {
            **DEFAULT_OPTIONS,
            "headers": self._get_auth_headers(),
            **options,
        }
        self.rest_url: str = f"{supabase_url}/rest/v1"
        self.realtime_url: str = f"{supabase_url}/realtime/v1".replace("http", "ws")
        self.auth_url: str = f"{supabase_url}/auth/v1"
        self.schema: str = settings.pop("schema")
        # Instantiate clients.
        self.auth: SupabaseAuthClient = self._init_supabase_auth_client(
            auth_url=self.auth_url, supabase_key=self.supabase_key, **settings,
        )
        # TODO(fedden): Bring up to parity with JS client.
        #  self.realtime: SupabaseRealtimeClient = self._init_realtime_client(
        #      realtime_url=self.realtime_url, supabase_key=self.supabase_key,
        #  )
        self.realtime = None
        self.postgrest: PostgrestClient = self._init_postgrest_client(
            rest_url=self.rest_url,
            supabase_key=supabase_key,
        )

    def table(self, table_name: str) -> SupabaseQueryBuilder:
        """Perform a table operation.

        Note that the supabase client uses the `from` method, but in Python,
        this is a reserved keyword so we have elected to use the name `table`.
        Alternatively you can use the `._from()` method.
        """
        return self.from_(table_name)

    def from_(self, table_name: str) -> SupabaseQueryBuilder:
        """Perform a table operation.

        See the `table` method.
        """
        query_builder = SupabaseQueryBuilder(
            url=f"{self.rest_url}/{table_name}",
            headers=self._get_auth_headers(),
            schema=self.schema,
            realtime=self.realtime,
            table=table_name,
        )
        return query_builder.from_(table_name)

    def rpc(self, fn, params):
        """Performs a stored procedure call.

        Parameters
        ----------
        fn : callable
            The stored procedure call to be executed.
        params : dict of any
            Parameters passed into the stored procedure call.

        Returns
        -------
        Response
            Returns the HTTP Response object which results from executing the
            call.
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

    async def _close_subscription(self, subscription):
        """Close a given subscription

        Parameters
        ----------
        subscription
            The name of the channel
        """
        if not subscription.closed:
            await self._closeChannel(subscription)

    def get_subscriptions(self):
        """Return all channels the the client is subscribed to."""
        return self.realtime.channels

    @staticmethod
    def _init_realtime_client(
        realtime_url: str, supabase_key: str
    ) -> SupabaseRealtimeClient:
        """Private method for creating an instance of the realtime-py client."""
        return SupabaseRealtimeClient(
            realtime_url, {"params": {"apikey": supabase_key}}
        )

    @staticmethod
    def _init_supabase_auth_client(
        auth_url: str,
        supabase_key: str,
        detect_session_in_url: bool,
        auto_refresh_token: bool,
        persist_session: bool,
        local_storage: Dict[str, Any],
        headers: Dict[str, str],
    ) -> SupabaseAuthClient:
        """Creates a wrapped instance of the GoTrue Client."""
        return SupabaseAuthClient(
            url=auth_url,
            auto_refresh_token=auto_refresh_token,
            detect_session_in_url=detect_session_in_url,
            persist_session=persist_session,
            local_storage=local_storage,
            headers=headers,
        )

    @staticmethod
    def _init_postgrest_client(rest_url: str, supabase_key: str) -> PostgrestClient:
        """Private helper for creating an instance of the Postgrest client."""
        client = PostgrestClient(rest_url)
        client.auth(token=supabase_key)
        return client

    def _get_auth_headers(self) -> Dict[str, str]:
        """Helper method to get auth headers."""
        # What's the corresponding method to get the token
        headers: Dict[str, str] = {
            "apiKey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
        }
        return headers


def create_client(supabase_url: str, supabase_key: str, **options) -> Client:
    """Create client function to instanciate supabase client like JS runtime.

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
    Instanciating the client.
    >>> import os
    >>> from supabase_py import create_client, Client
    >>>
    >>> url: str = os.environ.get("SUPABASE_TEST_URL")
    >>> key: str = os.environ.get("SUPABASE_TEST_KEY")
    >>> supabase: Client = create_client(url, key)

    Returns
    -------
    Client
    """
    return Client(supabase_url=supabase_url, supabase_key=supabase_key, **options)
