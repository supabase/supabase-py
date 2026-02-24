from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, List, Optional

from httpx import Headers, QueryParams
from supabase_utils.http import (
    EmptyRequest,
    HttpIO,
    HttpMethod,
    JSONRequest,
    handle_http_io,
)
from supabase_utils.types import JSON
from yarl import URL

from .helpers import (
    model_validate,
    parse_link_response,
    parse_user_response,
    redirect_to_as_query,
    validate_uuid,
)
from .types import (
    AdminUserAttributes,
    AuthMFAAdminDeleteFactorResponse,
    AuthMFAAdminListFactorsResponse,
    CreateOAuthClientParams,
    GenerateLinkParams,
    GenerateLinkResponse,
    OAuthClient,
    OAuthClientListResponse,
    OAuthClientResponse,
    SignOutScope,
    UpdateOAuthClientParams,
    User,
    UserList,
    UserResponse,
)


@dataclass
class SupabaseAuthAdminMFA(Generic[HttpIO]):
    """
    Contains the full multi-factor authentication administration API.
    """

    executor: HttpIO
    base_url: URL

    @handle_http_io
    def delete_factor(
        self,
        id: str,
        user_id: str,
    ) -> HttpMethod[AuthMFAAdminDeleteFactorResponse]:
        """
        Deletes a factor on a user. This will log the user out of all active
        sessions (if the deleted factor was verified). There's no need to delete
        unverified factors.
        """
        validate_uuid(user_id)
        validate_uuid(id)
        response = yield EmptyRequest(
            method="DELETE",
            path=["admin","users", user_id, "factors", id],
        )
        return model_validate(AuthMFAAdminDeleteFactorResponse, response.content)
    
    @handle_http_io
    def list_factors(
        self,
        user_id: str
    ) -> HttpMethod[AuthMFAAdminListFactorsResponse]:
        """
        Lists all factors attached to a user.
        """
        validate_uuid(user_id)
        response = yield EmptyRequest(
            method="GET",
            path=["admin","users", user_id, "factors"],
        )
        return model_validate(AuthMFAAdminListFactorsResponse, response.content)

@dataclass
class SupabaseAuthAdminOAuth(Generic[HttpIO]):
    """
    Contains all OAuth client administration methods.
    Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.
    """

    executor: HttpIO
    base_url: URL

    @handle_http_io
    def list_clients(
        self,
        page: int | None = None,
        per_page: int | None = None,
    ) -> HttpMethod[OAuthClientListResponse]:
        """
        Lists all OAuth clients with optional pagination.
        Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        query = QueryParams(page=page, per_page=per_page)
        response = yield EmptyRequest(
            method="GET",
            path=["admin", "oauth", "clients"],
            query_params=query,
        )

        result = model_validate(OAuthClientListResponse, response.content)

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


    @handle_http_io
    def create_client(
        self,
        params: CreateOAuthClientParams,
    ) -> HttpMethod[OAuthClientResponse]:
        """
        Creates a new OAuth client.
        Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        response = yield JSONRequest(
            method="POST",
            path=["admin", "oauth", "clients"],
            body=params,
        )

        return OAuthClientResponse(client=model_validate(OAuthClient, response.content))

    @handle_http_io
    def get_client(
        self,
        client_id: str,
    ) -> HttpMethod[OAuthClientResponse]:
        """
        Gets details of a specific OAuth client.
        Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        validate_uuid(client_id)
        response = yield EmptyRequest(
            method="GET",
            path=["admin", "oauth", "clients", client_id],
        )
        return OAuthClientResponse(client=model_validate(OAuthClient, response.content))

    @handle_http_io
    def update_client(
        self,
        client_id: str,
        params: UpdateOAuthClientParams,
    ) -> HttpMethod[OAuthClientResponse]:
        """
        Updates an OAuth client.
        Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        validate_uuid(client_id)
        response = yield JSONRequest(
            method="PUT",
            path=["admin", "oauth", "clients", client_id],
            body=params,
        )
        return OAuthClientResponse(client=model_validate(OAuthClient, response.content))

    @handle_http_io
    def delete_client(
        self,
        client_id: str,
    ) -> HttpMethod[None]:
        """
        Deletes an OAuth client.
        Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        validate_uuid(client_id)
        yield EmptyRequest(
            method="DELETE",
            path=["admin", "oauth", "clients", client_id],
        )

    @handle_http_io
    def regenerate_client_secret(
        self,
        client_id: str,
    ) -> HttpMethod[OAuthClientResponse]:
        """
        Regenerates the secret for an OAuth client.
        Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        validate_uuid(client_id)
        response = yield EmptyRequest(
            method="POST",
            path=["admin", "oauth", "clients", client_id, "regenerate_secret"],
        )
        return OAuthClientResponse(client=model_validate(OAuthClient, response.content))


class SupabaseAuthAdmin(Generic[HttpIO]):
    def __init__(
        self,
        executor: HttpIO,
        base_url: URL,
    ) -> None:
        self.executor: HttpIO = executor
        self.base_url: URL = base_url
        
        self.mfa: SupabaseAuthAdminMFA[HttpIO] = SupabaseAuthAdminMFA(self.executor, self.base_url)
        self.oauth: SupabaseAuthAdminOAuth[HttpIO] = SupabaseAuthAdminOAuth(self.executor, self.base_url)

    @handle_http_io
    def sign_out(self, jwt: str, scope: SignOutScope = "global") -> HttpMethod[None]:
        """
        Removes a logged-in session.
        """
        yield EmptyRequest(
            method="POST",
            path=["logout"],
            query_params=QueryParams(scope=scope),
            headers=Headers({"Authorization": f"Bearer {jwt}"})
        )

    @handle_http_io
    def invite_user_by_email(
        self,
        email: str,
        redirect_to: str | None = None,
        data: JSON | None = None,
    ) -> HttpMethod[UserResponse]:
        """
        Sends an invite link to an email address.
        """
        response = yield JSONRequest(
            method="POST",
            path=["invite"],
            body={"email": email, "data": data},
            query_params=redirect_to_as_query(redirect_to),
        )
        return parse_user_response(response)

    @handle_http_io
    def generate_link(self, params: GenerateLinkParams) -> HttpMethod[GenerateLinkResponse]:
        """
        Generates email links and OTPs to be sent via a custom email provider.
        """
        response = yield JSONRequest(
            method="POST",
            path=["admin", "generate_link"],
            body=params.body,
            query_params=redirect_to_as_query(params.redirect_to),
        )

        return parse_link_response(response)

    # User Admin API

    @handle_http_io
    def create_user(self, attributes: AdminUserAttributes) -> HttpMethod[UserResponse]:
        """
        Creates a new user.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        response = yield JSONRequest(
            method="POST",
            path=["admin", "users"],
            body=attributes,
            exclude_none=True
        )
        return parse_user_response(response)

    @handle_http_io
    def list_users(
        self, page: Optional[int] = None, per_page: Optional[int] = None
    ) -> HttpMethod[List[User]]:
        """
        Get a list of users.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        response = yield EmptyRequest(
            method="GET",
            path=["admin", "users"],
            query_params=QueryParams(page=page, per_page=per_page),
        )
        return model_validate(UserList, response.content).users

    @handle_http_io
    def get_user_by_id(self, uid: str) -> HttpMethod[UserResponse]:
        """
        Get user by id.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        validate_uuid(uid)

        response = yield EmptyRequest(
            method="GET",
            path=["admin", "users", uid],
        )
        return parse_user_response(response)

    @handle_http_io
    def update_user_by_id(
        self,
        uid: str,
        attributes: AdminUserAttributes,
    ) -> HttpMethod[UserResponse]:
        """
        Updates the user data.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        validate_uuid(uid)
        response = yield JSONRequest(
            method="PUT",
            path=["admin", "users", uid],
            body=attributes,
        )
        return parse_user_response(response)

    @handle_http_io
    def delete_user(self, id: str, should_soft_delete: bool = False) -> HttpMethod[None]:
        """
        Delete a user. Requires a `service_role` key.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        validate_uuid(id)
        body = {"should_soft_delete": should_soft_delete}
        yield JSONRequest(method="DELETE", path=["admin", "users", id], body=body)


