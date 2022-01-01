from typing import Dict, Optional

from gotrue import (
    CookieOptions,
    SyncGoTrueAPI,
    SyncGoTrueClient,
    SyncMemoryStorage,
    SyncSupportedStorage,
)
from gotrue.constants import COOKIE_OPTIONS


class SupabaseAuthClient(SyncGoTrueClient):
    """SupabaseAuthClient"""

    def __init__(
        self,
        *,
        url: str,
        headers: Dict[str, str] = {},
        auto_refresh_token: bool = True,
        persist_session: bool = True,
        local_storage: SyncSupportedStorage = SyncMemoryStorage(),
        cookie_options: CookieOptions = CookieOptions.parse_obj(COOKIE_OPTIONS),
        api: Optional[SyncGoTrueAPI] = None,
        replace_default_headers: bool = False,
    ):
        """Instanciate SupabaseAuthClient instance."""
        SyncGoTrueClient.__init__(
            self,
            url=url,
            headers=headers,
            auto_refresh_token=auto_refresh_token,
            persist_session=persist_session,
            local_storage=local_storage,
            cookie_options=cookie_options,
            api=api,
            replace_default_headers=replace_default_headers,
        )
