class SupabaseClient():
    def __init__(self, supabaseUrl: str, supabaseKey: str):
        if not supabaseUrl or not supabaseKey:
            raise("supabaseUrl is required")
        self.restUrl = f"{supabaseUrl}/rest/v1"
        self.realtimeUrl = f"{supabaseUrl}/realtime/v1".replace('http', 'ws')
        self.authUrl = f"{supabaseUrl}/auth/v1"


    def some_other_stuff(self):
        pass

    def auth(self):
        pass

    def rpc(self):

        pass

    def removeSubscription(self):
        pass
    
    def _closeSubscription(self, subscription):
        pass

    def getSubscriptions(self):
        pass

    def _initSupabaseAuthClient(self):
        pass

    def _initSupabaseAuthClient(self):
        pass
    
    def _initPostgRESTClient(self):
        pass
    
    def  _getAuthHeaders(self):
        pass
    
    def _closeChannel(self):
        pass

