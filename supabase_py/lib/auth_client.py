import gotrue

from typing import Any, Dict, Optional

# TODO(fedden): What are the correct types here?
class SupabaseAuthClient(gotrue.Client):
    """SupabaseAuthClient"""

    def __init__(
        self,
        auth_url: str,
        detect_session_url: bool = False,
        auto_refresh_token: bool = False,
        persist_session: bool = False,
        local_storage: Optional[Dict[str, Any]] = None,
        headers: Optional[Any] = None,
    ):
        """Instanciate SupabaseAuthClient instance."""
        super().__init__(auth_url)
        self.headers = headers
        self.detect_session_url = detect_session_url
        self.auto_refresh_token = auto_refresh_token
        self.persist_session = persist_session
        self.local_storage = local_storage
