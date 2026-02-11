
from httpx import Client
from supabase_auth import (
    AuthFlowType,
    SyncGoTrueClient,
    SyncSupportedStorage,
)


class SyncSupabaseAuthClient(SyncGoTrueClient):
    """Supabase Auth Client for synchronous operations."""

    def __init__(
        self,
        *,
        url: str,
        headers: dict[str, str] | None = None,
        storage_key: str | None = None,
        auto_refresh_token: bool = True,
        persist_session: bool = True,
        storage: SyncSupportedStorage | None = None,
        http_client: Client | None = None,
        flow_type: AuthFlowType = "implicit",
        verify: bool = True,
        proxy: str | None = None,
    ) -> None:
        """
        Instantiate a SupabaseAuthClient instance.

        Args:
            url (str): The URL of the Supabase instance.
            headers (Optional[dict[str, str]]): Optional headers to include in requests.
            storage_key (Optional[str]): Key to store session information.
            auto_refresh_token (bool): Whether to automatically refresh the token. Defaults to True.
            persist_session (bool): Whether to persist the session. Defaults to True.
            storage (SyncSupportedStorage): Storage mechanism. Defaults to SyncMemoryStorage().
            http_client (Optional[SyncClient]): HTTP client for making requests. Defaults to None.
            flow_type (AuthFlowType): Type of authentication flow. Defaults to "implicit".
            verify (bool): Whether to verify SSL certificates. Defaults to True.
            proxy (Optional[str]): Proxy URL. Defaults to None.
        """
        if headers is None:
            headers = {}

        super().__init__(
            url=url,
            headers=headers,
            storage_key=storage_key,
            auto_refresh_token=auto_refresh_token,
            persist_session=persist_session,
            storage=storage,
            http_client=http_client,
            flow_type=flow_type,
            verify=verify,
            proxy=proxy,
        )
