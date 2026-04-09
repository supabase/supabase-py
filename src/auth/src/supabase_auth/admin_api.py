from __future__ import annotations

from dataclasses import dataclass
from types import TracebackType
from typing import Generic, List

from supabase_utils.http.headers import Headers
from supabase_utils.http.io import (
    AsyncHttpIO,
    AsyncHttpSession,
    HttpIO,
    HttpMethod,
    HttpSession,
    SyncHttpIO,
    handle_http_io,
)
from supabase_utils.http.query import URLQuery
from supabase_utils.http.request import EmptyRequest, JSONRequest
from supabase_utils.types import JSON
from yarl import URL

from .helpers import (
    handle_error_response,
    parse_link_response,
    parse_user_response,
    redirect_to_as_query,
    validate_adapter,
    validate_model,
    validate_uuid,
)
from .types import (
    AdminUserAttributes,
    AuthMFAAdminDeleteFactorResponse,
    AuthMFAAdminListFactorsResponse,
    AuthMFAAdminListFactorsResponseParser,
    CreateOAuthClientParams,
    GenerateLinkParams,
    GenerateLinkResponse,
    OAuthClient,
    OAuthClientListResponse,
    OAuthClientResponse,
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
    default_headers: Headers

    @handle_http_io
    def delete_factor(
        self,
        factor_id: str,
        user_id: str,
    ) -> HttpMethod[AuthMFAAdminDeleteFactorResponse]:
        """
        Deletes a factor on a user. This will log the user out of all active
        sessions (if the deleted factor was verified). There's no need to delete
        unverified factors.
        """
        validate_uuid(user_id)
        validate_uuid(factor_id)
        response = yield EmptyRequest(
            method="DELETE",
            path=["admin", "users", user_id, "factors", factor_id],
        )
        return validate_model(response, AuthMFAAdminDeleteFactorResponse)

    @handle_http_io
    def list_factors(self, user_id: str) -> HttpMethod[AuthMFAAdminListFactorsResponse]:
        """
        Lists all factors attached to a user.
        """
        validate_uuid(user_id)
        response = yield EmptyRequest(
            method="GET",
            path=["admin", "users", user_id, "factors"],
        )
        return validate_adapter(response, AuthMFAAdminListFactorsResponseParser)


@dataclass
class SupabaseAuthAdminOAuth(Generic[HttpIO]):
    """
    Contains all OAuth client administration methods.
    Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.
    """

    executor: HttpIO
    base_url: URL
    default_headers: Headers

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
        query = URLQuery.from_mapping(
            {
                "page": page if page is not None else "",
                "per_page": per_page if per_page is not None else "",
            }
        )
        response = yield EmptyRequest(
            method="GET",
            path=["admin", "oauth", "clients"],
            query=query,
        )

        result = validate_model(response, OAuthClientListResponse)

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

        return OAuthClientResponse(client=validate_model(response, OAuthClient))

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
        return OAuthClientResponse(client=validate_model(response, OAuthClient))

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
        return OAuthClientResponse(client=validate_model(response, OAuthClient))

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
        response = yield EmptyRequest(
            method="DELETE",
            path=["admin", "oauth", "clients", client_id],
        )
        if not response.is_success:
            raise handle_error_response(response)

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
        return OAuthClientResponse(client=validate_model(response, OAuthClient))


class SupabaseAuthAdmin(Generic[HttpIO]):
    def __init__(
        self, executor: HttpIO, base_url: URL, default_headers: Headers
    ) -> None:
        self.executor: HttpIO = executor
        self.base_url: URL = base_url
        self.default_headers: Headers = default_headers

        self.mfa: SupabaseAuthAdminMFA[HttpIO] = SupabaseAuthAdminMFA(
            self.executor, self.base_url, default_headers
        )
        self.oauth: SupabaseAuthAdminOAuth[HttpIO] = SupabaseAuthAdminOAuth(
            self.executor, self.base_url, default_headers
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
            query=redirect_to_as_query(redirect_to),
        )
        return parse_user_response(response)

    @handle_http_io
    def generate_link(
        self, params: GenerateLinkParams
    ) -> HttpMethod[GenerateLinkResponse]:
        """
        Generates email links and OTPs to be sent via a custom email provider.
        """
        response = yield JSONRequest(
            method="POST",
            path=["admin", "generate_link"],
            body=params.body,
            query=redirect_to_as_query(params.redirect_to),
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
            method="POST", path=["admin", "users"], body=attributes, exclude_none=True
        )
        return parse_user_response(response)

    @handle_http_io
    def list_users(
        self, page: int | None = None, per_page: int | None = None
    ) -> HttpMethod[List[User]]:
        """
        Get a list of users.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        query = URLQuery.from_mapping(
            {
                "page": page if page is not None else "",
                "per_page": per_page if per_page is not None else "",
            }
        )
        response = yield EmptyRequest(
            method="GET",
            path=["admin", "users"],
            query=query,
        )
        return validate_model(response, UserList).users

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
    def delete_user(
        self, id: str, should_soft_delete: bool = False
    ) -> HttpMethod[None]:
        """
        Delete a user. Requires a `service_role` key.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        validate_uuid(id)
        body = {"should_soft_delete": should_soft_delete}
        response = yield JSONRequest(
            method="DELETE", path=["admin", "users", id], body=body
        )
        if not response.is_success:
            raise handle_error_response(response)


class SyncSupabaseAuthAdmin(SupabaseAuthAdmin[SyncHttpIO]):
    def __init__(
        self,
        url: str,
        http_session: HttpSession,
        default_headers: dict[str, str] | None = None,
    ) -> None:
        SupabaseAuthAdmin.__init__(
            self,
            executor=SyncHttpIO(session=http_session),
            base_url=URL(url),
            default_headers=Headers.from_mapping(default_headers)
            if default_headers
            else Headers.empty(),
        )

    def __enter__(self) -> SyncSupabaseAuthAdmin:
        self.executor.session.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[Exception] | None,
        exc: Exception | None,
        tb: TracebackType | None,
    ) -> None:
        self.executor.session.__exit__(exc_type, exc, tb)


class AsyncSupabaseAuthAdmin(SupabaseAuthAdmin[AsyncHttpIO]):
    def __init__(
        self,
        url: str,
        http_session: AsyncHttpSession,
        default_headers: dict[str, str] | None = None,
    ) -> None:
        SupabaseAuthAdmin.__init__(
            self,
            executor=AsyncHttpIO(session=http_session),
            base_url=URL(url),
            default_headers=Headers.from_mapping(default_headers)
            if default_headers
            else Headers.empty(),
        )

    async def __aenter__(self) -> AsyncSupabaseAuthAdmin:
        await self.executor.session.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[Exception] | None,
        exc: Exception | None,
        tb: TracebackType | None,
    ) -> None:
        await self.executor.session.__aexit__(exc_type, exc, tb)
