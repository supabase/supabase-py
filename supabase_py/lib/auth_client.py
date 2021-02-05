import gotrue

from typing import Any, Dict, Optional

# TODO(fedden): What are the correct types here?
class SupabaseAuthClient(gotrue.Client):
    """SupabaseAuthClient"""

    def __init__(
        self,
        authURL: str,
        detectSessionInUrl: bool = False,
        autoRefreshToken: bool = False,
        persistSession: bool = False,
        localStorage: Optional[Dict[str, Any]] = None,
        headers: Optional[Any] = None,
    ):
        """Instanciate SupabaseAuthClient instance."""
        super().__init__(authURL)
        self.headers = headers
        self.detectSessionInUrl = detectSessionInUrl
        self.autoRefreshToken = autoRefreshToken
        self.persistSession = persistSession
        self.localStorage = localStorage
