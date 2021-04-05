from typing import Any, Dict, Optional

import gotrue


class SupabaseAuthClient(gotrue.Client):
    """SupabaseAuthClient"""

    def __init__(
        self,
        url: str,
        detect_session_in_url: bool = False,
        auto_refresh_token: bool = False,
        persist_session: bool = False,
        local_storage: Optional[Dict[str, Any]] = None,
        headers: Dict[str, str] = {},
    ):
        """Instanciate SupabaseAuthClient instance."""
        super().__init__(
            url=url,
            headers=headers,
            detect_session_in_url=detect_session_in_url,
            auto_refresh_token=auto_refresh_token,
            persist_session=persist_session,
            local_storage=local_storage,
        )
