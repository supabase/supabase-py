import gotrue

from postgrest_py import PostgrestClient
from .lib.supabase_auth_client import SupabaseAuthClient
from .lib.supabase_realtime_client import SupabaseRealtimeClient
from .lib.supabase_query_builder import SupabaseQueryBuilder
from typing import Optional


DEFAULT_OPTIONS = {
    "schema": "public",
    "auto_refresh_token": True,
    "persist_session": True,
    "detect_session_in_url": True,
    "headers": {},
}


class Client:
    def __init__(
        self, supabaseUrl: str, supabaseKey: str, options: Optional[dict] = {}
    ):
        """
        Initialize a Supabase Client
        Parameters
        ----------
        SupabaseUrl
            URL of the Supabase instance that we are acting on
        SupabaseKey
            API key for the Supabase instance that we are acting on
        Options
            Any other settings that we wish to override

        Returns
        None
        -------
        """
        if not supabaseUrl:
            raise Exception("supabaseUrl is required")
        if not supabaseKey:
            raise Exception("supabaseKey is required")

        settings = {**DEFAULT_OPTIONS, **options}
        self.restUrl = f"{supabaseUrl}/rest/v1"
        self.realtimeUrl = f"{supabaseUrl}/realtime/v1".replace("http", "ws")
        self.authUrl = f"{supabaseUrl}/auth/v1"
        self.schema = settings["schema"]
        self.supabaseUrl = supabaseUrl
        self.supabaseKey = supabaseKey
        self.auth = self._initSupabaseAuthClient(*settings)
        # TODO: Fix this once Realtime-py is working
        # self.realtime = self._initRealtimeClient()

    def _from(self, table: str):
        """
        Perform a table operation on a given table
        Parameters
        ----------
        table
            Name of table to execute operations on
        Returns
        -------
        SupabaseQueryBuilder
        Wrapper for Postgrest-py client which we can perform operations(e.g. select/update) with
        """
        url = f"{self.restUrl}/{table}"
        return SupabaseQueryBuilder(
            url,
            {
                "headers": self._getAuthHeaders(),
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

    # TODO: Fix this segment after realtime-py is working
    # def removeSubscription(self, subscription):
    #     async def remove_subscription_helper(resolve):
    #         try:
    #             await self._closeSubscription(subscription)
    #             openSubscriptions = len(self.getSubscriptions())
    #             if not openSubscriptions:
    #                 error = await self.realtime.disconnect()
    #                 if error:
    #                     return {"error": None, "data": { openSubscriptions}}
    #         except Error as e:
    #             return {error}

    #     return remove_subscription_helper(subscription)

    async def _closeSubscription(self, subscription):
        """
        Close a given subscription

        Parameters
        ----------
        subscription
            The name of the channel
        """
        if not subscription.closed:
            await self._closeChannel(subscription)

    def getSubscriptions(self):
        """
        Return all channels the the client is subscribed to.
        """
        return self.realtime.channels

    def _initRealtimeClient(self):
        """
        Private method for creating an instance of the realtime-py client.
        """
        return RealtimeClient(self.realtimeUrl, {"params": {apikey: self.supabaseKey}})

    def _initSupabaseAuthClient(
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

    def _initPostgrestClient(self):
        """
        Private helper method for creating a wrapped instance of the Postgrest client.
        """
        return PostgrestClient(self.restUrl)

    def _getAuthHeaders(self):
        """
        Helper method to get auth headers
        """
        headers = {}
        # TODO: Add way of getting auth token
        headers["apiKey"] = self.supabaseKey
        headers["Authorization"] = f"Bearer {self.supabaseKey}"
        return headers

    # TODO: Fix this segment after realtime-py is working
    # def closeSubscription(self):
    #     if not subscription.closed:
    #         await self._closeChannel(subscription)

    # def _closeChannel(self, subscription):
    #     async def _closeChannelHelper():
    #         subscription.unsubscribe().on('OK')
