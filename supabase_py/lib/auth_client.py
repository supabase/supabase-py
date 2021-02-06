from typing import Any, Dict, Optional

import gotrue


class SupabaseAuthClient(gotrue.Client):
    """SupabaseAuthClient"""

    def __init__(
        self,
        auth_url: str,
        detect_session_url: bool = False,
        auto_refresh_token: bool = False,
        persist_session: bool = False,
        local_storage: Optional[Dict[str, Any]] = None,
        headers: Dict[str, str] = {},
    ):
        """Instanciate SupabaseAuthClient instance."""
        super().__init__(auth_url)
        self.headers = headers
        self.detect_session_url = detect_session_url
        self.auto_refresh_token = auto_refresh_token
        self.persist_session = persist_session
        self.local_storage = local_storage
        self.jwt = None

    def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """Sign in with email and password."""
        response = super().sign_in(credentials={"email": email, "password": password})
        # TODO(fedden): Log JWT to self.jwt
        return response

    def sign_up(self, email: str, password: str) -> Dict[str, Any]:
        """Sign up with email and password."""
        response = super().sign_up(credentials={"email": email, "password": password})
        # TODO(fedden): Log JWT to self.jwt
        return response

    def sign_out(self) -> Dict[str, Any]:
        """Sign out of logged in user."""
        if self.jwt is None:
            raise ValueError("Cannot sign out if not signed in.")
        response = super().sign_out(jwt=self.jwt)
        self.jwt = None
        return response.json()
