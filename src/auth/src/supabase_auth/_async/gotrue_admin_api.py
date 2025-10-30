from __future__ import annotations

from typing import Any, Dict, List, Optional

from httpx import QueryParams, Response
from pydantic import TypeAdapter

from ..helpers import (
    validate_uuid,
    model_validate,
    parse_link_response,
    parse_user_response,
)
from ..http_clients import AsyncClient
from ..types import (
    AdminUserAttributes,
    AuthMFAAdminDeleteFactorParams,
    AuthMFAAdminDeleteFactorResponse,
    AuthMFAAdminListFactorsParams,
    AuthMFAAdminListFactorsResponse,
    CreateOAuthClientParams,
    GenerateLinkParams,
    GenerateLinkResponse,
    InviteUserByEmailOptions,
    OAuthClient,
    OAuthClientListResponse,
    OAuthClientResponse,
    PageParams,
    SignOutScope,
    User,
    UserList,
    UserResponse,
)
from .gotrue_admin_mfa_api import AsyncGoTrueAdminMFAAPI
from .gotrue_admin_oauth_api import AsyncGoTrueAdminOAuthAPI
from .gotrue_base_api import AsyncGoTrueBaseAPI


class AsyncGoTrueAdminAPI(AsyncGoTrueBaseAPI):
    def __init__(
        self,
        *,
        url: str = "",
        headers: Dict[str, str] = {},
        http_client: Optional[AsyncClient] = None,
        verify: bool = True,
        proxy: Optional[str] = None,
    ) -> None:
        AsyncGoTrueBaseAPI.__init__(
            self,
            url=url,
            headers=headers,
            http_client=http_client,
            verify=verify,
            proxy=proxy,
        )
        # TODO(@o-santi): why is is this done this way?
        self.mfa = AsyncGoTrueAdminMFAAPI()
        self.mfa.list_factors = self._list_factors # type: ignore
        self.mfa.delete_factor = self._delete_factor # type: ignore
        self.oauth = AsyncGoTrueAdminOAuthAPI()
        self.oauth.list_clients = self._list_oauth_clients # type: ignore
        self.oauth.create_client = self._create_oauth_client # type: ignore
        self.oauth.get_client = self._get_oauth_client # type: ignore
        self.oauth.delete_client = self._delete_oauth_client # type: ignore
        self.oauth.regenerate_client_secret = self._regenerate_oauth_client_secret # type: ignore

    async def sign_out(self, jwt: str, scope: SignOutScope = "global") -> None:
        """
        Removes a logged-in session.
        """
        await self._request(
            "POST",
            "logout",
            query=QueryParams(scope=scope),
            jwt=jwt,
            no_resolve_json=True,
        )

    async def invite_user_by_email(
        self,
        email: str,
        options: InviteUserByEmailOptions = {},
    ) -> UserResponse:
        """
        Sends an invite link to an email address.
        """
        response = await self._request(
            "POST",
            "invite",
            body={"email": email, "data": options.get("data")},
            redirect_to=options.get("redirect_to"),
        )
        return parse_user_response(response)

    async def generate_link(self, params: GenerateLinkParams) -> GenerateLinkResponse:
        """
        Generates email links and OTPs to be sent via a custom email provider.
        """
        response = await self._request(
            "POST",
            "admin/generate_link",
            body={
                "type": params.get("type"),
                "email": params.get("email"),
                "password": params.get("password"),
                "new_email": params.get("new_email"),
                "data": params.get("options", {}).get("data"),
            },
            redirect_to=params.get("options", {}).get("redirect_to"),
        )

        return parse_link_response(response)

    # User Admin API

    async def create_user(self, attributes: AdminUserAttributes) -> UserResponse:
        """
        Creates a new user.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        response = await self._request(
            "POST",
            "admin/users",
            body=attributes,
        )
        return parse_user_response(response)

    async def list_users(
        self, page: Optional[int] = None, per_page: Optional[int] = None
    ) -> List[User]:
        """
        Get a list of users.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        response = await self._request(
            "GET",
            "admin/users",
            query=QueryParams(page=page, per_page=per_page),
        )
        return model_validate(UserList, response.content).users

    async def get_user_by_id(self, uid: str) -> UserResponse:
        """
        Get user by id.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        validate_uuid(uid)

        response = await self._request(
            "GET",
            f"admin/users/{uid}",
        )
        return parse_user_response(response)

    async def update_user_by_id(
        self,
        uid: str,
        attributes: AdminUserAttributes,
    ) -> UserResponse:
        """
        Updates the user data.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        validate_uuid(uid)
        response = await self._request(
            "PUT",
            f"admin/users/{uid}",
            body=attributes,
        )
        return parse_user_response(response)

    async def delete_user(self, id: str, should_soft_delete: bool = False) -> None:
        """
        Delete a user. Requires a `service_role` key.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        validate_uuid(id)
        body = {"should_soft_delete": should_soft_delete}
        await self._request("DELETE", f"admin/users/{id}", body=body)

    async def _list_factors(
        self,
        params: AuthMFAAdminListFactorsParams,
    ) -> AuthMFAAdminListFactorsResponse:
        validate_uuid(params.get("user_id"))
        response = await self._request(
            "GET",
            f"admin/users/{params.get('user_id')}/factors",
        )
        return model_validate(AuthMFAAdminListFactorsResponse, response.content)

    async def _delete_factor(
        self,
        params: AuthMFAAdminDeleteFactorParams,
    ) -> AuthMFAAdminDeleteFactorResponse:
        validate_uuid(params.get("user_id"))
        validate_uuid(params.get("id"))
        response = await self._request(
            "DELETE",
            f"admin/users/{params.get('user_id')}/factors/{params.get('id')}",
        )
        return model_validate(AuthMFAAdminDeleteFactorResponse, response.content)

    async def _list_oauth_clients(
        self,
        params: PageParams | None = None,
    ) -> OAuthClientListResponse:
        """
        Lists all OAuth clients with optional pagination.
        Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        if params:
            query = QueryParams(page=params.page, per_page=params.per_page)
        else:
            query = None
        response = await self._request(
            "GET",
            "admin/oauth/clients",
            query=query,
            no_resolve_json=True,
        )

        data = response.json()
        # API may return either a list directly or a dict with "clients" key
        clients_data = data.get("clients", data) if isinstance(data, dict) else data
        result = OAuthClientListResponse(
            clients=[model_validate(OAuthClient, client) for client in clients_data],
            aud=data.get("aud") if isinstance(data, dict) else None,
        )

        # Parse pagination headers
        total = response.headers.get("x-total-count")
        if total:
            result.total = int(total)

        links = response.headers.get("link")
        if links:
            for link in links.split(","):
                parts = link.split(";")
                if len(parts) >= 2:
                    page_match = parts[0].split("page=")
                    if len(page_match) >= 2:
                        page_num = int(page_match[1].split("&")[0].rstrip(">"))
                        rel = parts[1].split("=")[1].strip('"')
                        if rel == "next":
                            result.next_page = page_num
                        elif rel == "last":
                            result.last_page = page_num

        return result

    async def _create_oauth_client(
        self,
        params: CreateOAuthClientParams,
    ) -> OAuthClientResponse:
        """
        Creates a new OAuth client.
        Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        response = await self._request(
            "POST",
            "admin/oauth/clients",
            body=params,
        )

        return OAuthClientResponse(
            client=model_validate(OAuthClient, response.content)
        )
    async def _get_oauth_client(
        self,
        client_id: str,
    ) -> OAuthClientResponse:
        """
        Gets details of a specific OAuth client.
        Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        validate_uuid(client_id)
        response = await self._request(
            "GET",
            f"admin/oauth/clients/{client_id}",
        )
        return OAuthClientResponse(
            client=model_validate(OAuthClient, response.content)
        )
    async def _delete_oauth_client(
        self,
        client_id: str,
    ) -> OAuthClientResponse:
        """
        Deletes an OAuth client.
        Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        validate_uuid(client_id)
        response = await self._request(
            "DELETE",
            f"admin/oauth/clients/{client_id}",
        )
        return OAuthClientResponse(
            client=model_validate(OAuthClient, response.content) if response.content else None
        )

    async def _regenerate_oauth_client_secret(
        self,
        client_id: str,
    ) -> OAuthClientResponse:
        """
        Regenerates the secret for an OAuth client.
        Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        validate_uuid(client_id)
        response = await self._request(
            "POST",
            f"admin/oauth/clients/{client_id}/regenerate_secret",
        )
        return OAuthClientResponse(
            client=model_validate(OAuthClient, response.content)
        )
