from postgrest_py import PostgrestClient
import gotrue

class Client():
    def __init__(self, supabaseUrl: str, supabaseKey: str):
        if not supabaseUrl or not supabaseKey:
            raise("supabaseUrl is required")
        SETTINGS = {}
        self.restUrl = f"{supabaseUrl}/rest/v1"
        self.realtimeUrl = f"{supabaseUrl}/realtime/v1".replace('http', 'ws')
        self.authUrl = f"{supabaseUrl}/auth/v1"
        # TODO: Allow user to pass in schema. This is hardcoded
        self.schema = 'public'
        self.supabaseUrl = supabaseUrl
        self.supabaseKey = supabaseKey
        # self.auth = self._initSupabaseAuthClient(SETTINGS)

    def _from(self, table: str):
        """
        Perform a table operation
        """
        pass

    def auth(self):
        pass

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
        # return RealtimeClient(self.realtimeUrl, {
        #     params: { apiKey: self.supabaseKey}
        # })

    def _initSupabaseAuthClient(self, autoRefreshToken, persistSession, 
    detectSessionInUrl,localStorage):
        pass
        # return SupabaseAuthClient({
        #     self.authUrl,
        #     "headers": {
        #         "Authorization": f"Bearer {self.supabaseKey}",
        #         "apiKey": f"{self.supabaseKey}",
        #         autoRefreshToken,
        #         persistSession,
        #         detectSessionInUrl,
        #         localStorage
        #     }
        # })
    
    def _initPostgrestClient(self):
        return PostgrestClient(self.restUrl)
    
    def  _getAuthHeaders(self):
        headers = {}
        # authBearer = self.auth.session().token if self.auth.session().token else self.supabaseKey
        headers['apiKey'] = self.supabaseKey
        headers['Authorization'] = f"Bearer {self.supabaseKey}"
        return headers
    
    def _closeChannel(self):
        pass

