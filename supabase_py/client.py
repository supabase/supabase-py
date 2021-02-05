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
        self.realtime = self._initRealtimeClient()

    def _from(self, table: str):
        """
        Perform a table operation
        """
        url = f"{self.restUrl}/{table}"
        return SupabaseQueryBuilder(
            url,
            {
                "headers": self._getAuthHeaders(),
                "schema": self.schema,
                "realtime": self.realtime,
            },
            table,
        )

    def rpc(self, fn, params):
        """
        Performs a stored procedure call.
        """
        rest = self._initPostgrestClient()
        return rest.rpc(fn, params)

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
        if not subscription.closed:
            await self._closeChannel(subscription)

    def getSubscriptions(self):
        return self.realtime.channels

    def _initRealtimeClient(self):
        return RealtimeClient(self.realtimeUrl, {"params": {apikey: self.supabaseKey}})

    def _initSupabaseAuthClient(
        self,
        schema,
        autoRefreshToken,
        persistSession,
        detectSessionInUrl,
        localStorage,
    ):
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
        return PostgrestClient(self.restUrl)

    def _getAuthHeaders(self):
        headers = {}
        # What's the corresponding method to get the token
        headers["apiKey"] = self.supabaseKey
        headers["Authorization"] = f"Bearer {self.supabaseKey}"
        return headers

    # def closeSubscription(self):
    #     if not subscription.closed:
    #         await self._closeChannel(subscription)

    # def _closeChannel(self, subscription):
    #     async def _closeChannelHelper():
    #         subscription.unsubscribe().on('OK')
