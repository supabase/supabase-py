import gotrue

from postgrest_py import PostgrestClient
from lib.auth_client import SupabaseAuthClient
from lib.realtime_client import SupabaseRealtimeClient
from lib.query_builder import SupabaseQueryBuilder

from typing import Any, Dict


DEFAULT_OPTIONS = {
    "schema": "public",
    "auto_refresh_token": True,
    "persist_session": True,
    "detect_session_in_url": True,
    "headers": {},
}


class Client:
    def __init__(
        self, supabase_url: str, supabase_key: str, **options,
    ):
        """Instanciate the client.

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
        settings: Dict[str, Any] = {**DEFAULT_OPTIONS, **options}
        self.restUrl = f"{supabase_url}/rest/v1"
        self.realtimeUrl = f"{supabase_url}/realtime/v1".replace("http", "ws")
        self.authUrl = f"{supabase_url}/auth/v1"
        self.schema = settings["schema"]
        self.supabaseUrl = supabase_url
        self.supabaseKey = supabase_key
        self.auth = self._init_supabase_auth_client(*settings)
        self.realtime = self._init_realtime_client()

    def _from(self, table: str):
        """Perform a table operation."""
        url = f"{self.rest_url}/{table}"
        return SupabaseQueryBuilder(
            url,
            {
                "headers": self._get_auth_headers(),
                "schema": self.schema,
                "realtime": self.realtime,
            },
            self.schema,
            self.realtime,
            table,
        )

    def rpc(self, fn, params):
        """
        Performs a stored procedure call.

        Parameters
        ----------
        fn
            The stored procedure call to be execured
        params
            Parameters passed into the stored procedure call

        Returns
        -------
        Response
        Returns the HTTP Response object which results from executing the call.
        """
        rest = self._initPostgrestClient()
        return rest.rpc(fn, params)

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
        """
        Close a given subscription

        Parameters
        ----------
        subscription
            The name of the channel
        """
        if not subscription.closed:
            await self._closeChannel(subscription)

    def get_subscriptions(self):
        """
        Return all channels the the client is subscribed to.
        """
        return self.realtime.channels

    def _init_realtime_client(self):
        """
        Private method for creating an instance of the realtime-py client.
        """
        return RealtimeClient(self.realtimeUrl, {"params": {apikey: self.supabaseKey}})

    def _init_supabase_auth_client(
        self,
        schema,
        autoRefreshToken,
        persistSession,
        detectSessionInUrl,
        localStorage,
    ):
        """
        Private helper method for creating a wrapped instance of the GoTrue Client.
        """
        return SupabaseAuthClient(
            self.authUrl,
            autoRefreshToken,
            persistSession,
            detectSessionInUrl,
            localStorage,
            headers={
                "Authorization": f"Bearer {self.supabaseKey}",
                "apikey": f"{self.supabaseKey}",
            },
        )

    def _init_postgrest_client(self):
        """
        Private helper method for creating a wrapped instance of the Postgrest client.
        """
        return PostgrestClient(self.restUrl)

    def _get_auth_headers(self):
        """
        Helper method to get auth headers
        """
        headers = {}
        # TODO: Add way of getting auth token
        headers["apiKey"] = self.supabaseKey
        headers["Authorization"] = f"Bearer {self.supabaseKey}"
        return headers
