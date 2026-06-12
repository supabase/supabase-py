from typing import TYPE_CHECKING, Optional

from ..types import (
    CreateOAuthClientParams,
    OAuthClientListResponse,
    OAuthClientResponse,
    PageParams,
    UpdateOAuthClientParams,
)

if TYPE_CHECKING:
    from .gotrue_admin_api import AsyncGoTrueAdminAPI


class AsyncGoTrueAdminOAuthAPI:
    """
    Contains all OAuth client administration methods.
    Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.
    """

    def __init__(self, root: "AsyncGoTrueAdminAPI"):
        self._root = root

    async def list_clients(
        self,
        params: Optional[PageParams] = None,
    ) -> OAuthClientListResponse:
        """
        Lists all OAuth clients with optional pagination.
        Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.

        This function should only be called on a server.
        Never expose your `secret` key in the browser.
        """
        return await self._root._list_oauth_clients(params)

    async def create_client(
        self,
        params: CreateOAuthClientParams,
    ) -> OAuthClientResponse:
        """
        Creates a new OAuth client.
        Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.

        This function should only be called on a server.
        Never expose your `secret` key in the browser.
        """
        return await self._root._create_oauth_client(params)

    async def get_client(
        self,
        client_id: str,
    ) -> OAuthClientResponse:
        """
        Gets details of a specific OAuth client.
        Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.

        This function should only be called on a server.
        Never expose your `secret` key in the browser.
        """
        return await self._root._get_oauth_client(client_id)

    async def update_client(
        self,
        client_id: str,
        params: UpdateOAuthClientParams,
    ) -> OAuthClientResponse:
        """
        Updates an OAuth client.
        Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.

        This function should only be called on a server.
        Never expose your `secret` key in the browser.
        """
        return await self._root._update_oauth_client(client_id, params)

    async def delete_client(
        self,
        client_id: str,
    ) -> OAuthClientResponse:
        """
        Deletes an OAuth client.
        Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.

        This function should only be called on a server.
        Never expose your `secret` key in the browser.
        """
        return await self._root._delete_oauth_client(client_id)

    async def regenerate_client_secret(
        self,
        client_id: str,
    ) -> OAuthClientResponse:
        """
        Regenerates the secret for an OAuth client.
        Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.

        This function should only be called on a server.
        Never expose your `secret` key in the browser.
        """
        return await self._root._regenerate_oauth_client_secret(client_id)
