from ..types import (
    CreateOAuthClientParams,
    OAuthClientListResponse,
    OAuthClientResponse,
    PageParams,
    UpdateOAuthClientParams,
)
from typing import Optional


class SyncGoTrueAdminOAuthAPI:
    """
    Contains all OAuth client administration methods.
    Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.
    """

    def list_clients(
        self,
        params: Optional[PageParams] = None,
    ) -> OAuthClientListResponse:
        """
        Lists all OAuth clients with optional pagination.
        Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        raise NotImplementedError()  # pragma: no cover

    def create_client(
        self,
        params: CreateOAuthClientParams,
    ) -> OAuthClientResponse:
        """
        Creates a new OAuth client.
        Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        raise NotImplementedError()  # pragma: no cover

    def get_client(
        self,
        client_id: str,
    ) -> OAuthClientResponse:
        """
        Gets details of a specific OAuth client.
        Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        raise NotImplementedError()  # pragma: no cover

    def update_client(
        self,
        client_id: str,
        params: UpdateOAuthClientParams,
    ) -> OAuthClientResponse:
        """
        Updates an OAuth client.
        Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        raise NotImplementedError()  # pragma: no cover

    def delete_client(
        self,
        client_id: str,
    ) -> OAuthClientResponse:
        """
        Deletes an OAuth client.
        Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        raise NotImplementedError()  # pragma: no cover

    def regenerate_client_secret(
        self,
        client_id: str,
    ) -> OAuthClientResponse:
        """
        Regenerates the secret for an OAuth client.
        Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        raise NotImplementedError()  # pragma: no cover
