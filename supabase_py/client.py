import gotrue

from postgrest_py import PostgrestClient
from .src.SupabaseAuthClient import SupabaseAuthClient
from .src.SupabaseRealtimeClient import SupabaseRealtimeClient
from .src.SupabaseQueryBuilder import SupabaseQueryBuilder
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

    def removeSubscription(self):
        pass

    def _closeSubscription(self, subscription):
        pass

    def getSubscriptions(self):
        pass

    def _initRealtimeClient(self):
        pass

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
        )

    def _initPostgrestClient(self):
        return PostgrestClient(self.restUrl)

    def _getAuthHeaders(self):
        headers = {}
        # What's the corresponding method to get the token
        # authBearer = self.auth.session().token if self.auth.session().token else self.supabaseKey
        headers["apiKey"] = self.supabaseKey
        headers["Authorization"] = f"Bearer {self.supabaseKey}"
        return headers

    def _closeChannel(self):
        pass
