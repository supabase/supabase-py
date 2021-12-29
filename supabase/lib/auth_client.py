from typing import Any, Dict

import gotrue


class SupabaseAuthClient(gotrue.Client):
    """SupabaseAuthClient"""

    def __init__(
        self,
        url: str,
        auto_refresh_token: bool = False,
        persist_session: bool = False,
        local_storage: Dict[str, Any] = {},
        headers: Dict[str, str] = {},
    ):
        """Instanciate SupabaseAuthClient instance."""
        super().__init__(
            url=url,
            headers=headers,
            auto_refresh_token=auto_refresh_token,
            persist_session=persist_session,
            local_storage=local_storage,
        )
