import gotrue
class SupabaseAuthClient(gotrue.Client):
    def __init__(self,authURL, headers=None, detectSessionInUrl=False, autoRefreshToken=False, persistSession=False, localStorage=None):
        super().__init__(authURL)
        self.headers = headers
        self.detectSessionInUrl = detectSessionInUrl
        self.autoRefreshToken = autoRefreshToken
        self.persistSession = persistSession
        self.localStorage = localStorage