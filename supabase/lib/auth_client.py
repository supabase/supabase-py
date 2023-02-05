from typing import Dict, Union

from gotrue import SyncGoTrueClient, SyncMemoryStorage, SyncSupportedStorage

# TODO - export this from GoTrue-py in next release
from httpx import Client as BaseClient


class SyncClient(BaseClient):
    def aclose(self) -> None:
        self.close()


class SupabaseAuthClient(SyncGoTrueClient):
    """SupabaseAuthClient"""

    def __init__(
        self,
        *,
        url: str,
        headers: Dict[str, str] = {},
        storage_key: Union[str, None] = None,
        auto_refresh_token: bool = True,
        persist_session: bool = True,
        storage: SyncSupportedStorage = SyncMemoryStorage(),
        http_client: Union[SyncClient, None] = None,
    ):
        """Instantiate SupabaseAuthClient instance."""
        SyncGoTrueClient.__init__(
            self,
            url=url,
            headers=headers,
            storage_key=storage_key,
            auto_refresh_token=auto_refresh_token,
            persist_session=persist_session,
            storage=storage,
            http_client=http_client,
        )
