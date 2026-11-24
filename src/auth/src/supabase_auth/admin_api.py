from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self

from supabase_utils.http.headers import Headers
from supabase_utils.http.io import (
    AsyncHttpIO,
    AsyncHttpSession,
    HttpMethod,
    HttpSession,
    SyncHttpIO,
    handle_http_io,
)
from supabase_utils.http.query import URLQuery
from supabase_utils.http.request import EmptyRequest, JSONRequest
from yarl import URL

from ._sign_out import _check_sign_out_scope, _logout
from .helpers import (
    _handle_error_response,
    _redirect_to_as_query,
    _validate_adapter,
    _validate_model,
    _validate_paginated_model,
    parse_link_response,
    parse_user_response,
    validate_uuid,
)
from .types import (
    AdminUserAttributes,
    AuthMFAAdminDeleteFactorResponse,
    AuthMFAAdminListFactorsResponse,
    AuthMFAAdminListFactorsResponseParser,
    CreateCustomProviderParams,
    CreateOAuthClientParams,
    CustomOAuthProvider,
    CustomProviderType,
    Factor,
    GenerateLinkParams,
    GenerateLinkResponse,
    OAuthClient,
    OAuthClientListResponse,
    OAuthClientResponse,
    SignOutScope,
    UpdateCustomProviderParams,
    UpdateOAuthClientParams,
    User,
    UserList,
    UserResponse,
    _CustomOAuthProviderList,
)
from .version import __version__

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator
    from types import TracebackType

    from supabase_utils.http.retry import RetryPolicy
    from supabase_utils.types import JSON


@dataclass
class SupabaseAuthAdminMFA[HttpIO: (SyncHttpIO, AsyncHttpIO)]:
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
        return _validate_model(response, AuthMFAAdminDeleteFactorResponse)

    @handle_http_io
    def update_factor(
        self,
        *,
        user_id: str,
        factor_id: str,
        friendly_name: str | None = None,
        phone: str | None = None,
    ) -> HttpMethod[Factor]:
        """
        Updates the friendly name of a factor on a user, or the phone number
        of a phone factor, and returns the updated factor. Only the given
        fields change.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        validate_uuid(user_id)
        validate_uuid(factor_id)
        body: dict[str, JSON] = {}
        if friendly_name is not None:
            body["friendly_name"] = friendly_name
        if phone is not None:
            body["phone"] = phone
        response = yield JSONRequest(
            method="PUT",
            path=["admin", "users", user_id, "factors", factor_id],
            body=body,
        )
        return _validate_model(response, Factor)

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
        return _validate_adapter(response, AuthMFAAdminListFactorsResponseParser)


@dataclass
class SupabaseAuthAdminOAuth[HttpIO: (SyncHttpIO, AsyncHttpIO)]:
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

        return _validate_paginated_model(response, OAuthClientListResponse)

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

        return OAuthClientResponse(client=_validate_model(response, OAuthClient))

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
        return OAuthClientResponse(client=_validate_model(response, OAuthClient))

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
        return OAuthClientResponse(client=_validate_model(response, OAuthClient))

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
            raise _handle_error_response(response)

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
        return OAuthClientResponse(client=_validate_model(response, OAuthClient))


def _validate_provider_identifier(identifier: str) -> None:
    if identifier in ("", ".", "..") or "/" in identifier:
        raise ValueError(f"Invalid custom provider identifier: {identifier!r}")


@dataclass
class SupabaseAuthAdminCustomProviders[HttpIO: (SyncHttpIO, AsyncHttpIO)]:
    """
    Contains the administration methods of custom OIDC and OAuth providers,
    the providers named with a `custom:` prefix, like `custom:mycompany`.
    These are distinct from the clients of the OAuth 2.1 server in `oauth`.
    """

    executor: HttpIO
    base_url: URL
    default_headers: Headers

    @handle_http_io
    def list_providers(
        self, provider_type: CustomProviderType | None = None
    ) -> HttpMethod[list[CustomOAuthProvider]]:
        """
        Lists all custom providers, or only those of `provider_type`.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        query = (
            URLQuery.from_mapping({"type": provider_type})
            if provider_type
            else URLQuery.empty()
        )
        response = yield EmptyRequest(
            method="GET",
            path=["admin", "custom-providers"],
            query=query,
        )
        return _validate_model(response, _CustomOAuthProviderList).providers

    @handle_http_io
    def create_provider(
        self, params: CreateCustomProviderParams
    ) -> HttpMethod[CustomOAuthProvider]:
        """
        Creates a custom OIDC or OAuth provider.

        For an OIDC provider, the server fetches and validates the discovery
        document of the issuer, or the one at `discovery_url`, and raises an
        `AuthApiError` with the code `validation_failed` when it cannot.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        response = yield JSONRequest(
            method="POST",
            path=["admin", "custom-providers"],
            body=params,
        )
        return _validate_model(response, CustomOAuthProvider)

    @handle_http_io
    def get_provider(self, identifier: str) -> HttpMethod[CustomOAuthProvider]:
        """
        Gets a custom provider by its identifier, like `custom:mycompany`.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        _validate_provider_identifier(identifier)
        response = yield EmptyRequest(
            method="GET",
            path=["admin", "custom-providers", identifier],
        )
        return _validate_model(response, CustomOAuthProvider)

    @handle_http_io
    def update_provider(
        self, identifier: str, params: UpdateCustomProviderParams
    ) -> HttpMethod[CustomOAuthProvider]:
        """
        Updates a custom provider by its identifier, like `custom:mycompany`.

        When the `issuer` or `discovery_url` of an OIDC provider changes, the
        server fetches and validates the discovery document again, and raises
        an `AuthApiError` with the code `validation_failed` when it cannot.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        _validate_provider_identifier(identifier)
        response = yield JSONRequest(
            method="PUT",
            path=["admin", "custom-providers", identifier],
            body=params,
        )
        return _validate_model(response, CustomOAuthProvider)

    @handle_http_io
    def delete_provider(self, identifier: str) -> HttpMethod[None]:
        """
        Deletes a custom provider by its identifier, like `custom:mycompany`.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        _validate_provider_identifier(identifier)
        response = yield EmptyRequest(
            method="DELETE",
            path=["admin", "custom-providers", identifier],
        )
        if not response.is_success:
            raise _handle_error_response(response)


class SupabaseAuthAdmin[HttpIO: (SyncHttpIO, AsyncHttpIO)]:
    def __init__(
        self, executor: HttpIO, base_url: URL, default_headers: Headers
    ) -> None:
        self.executor: HttpIO = executor
        self.base_url: URL = base_url
        supabase_headers = Headers.supabase_client_headers("supabase_auth", __version__)
        default_headers = supabase_headers.update(default_headers)
        self.default_headers: Headers = default_headers

        self.mfa: SupabaseAuthAdminMFA[HttpIO] = SupabaseAuthAdminMFA(
            self.executor, self.base_url, default_headers
        )
        self.oauth: SupabaseAuthAdminOAuth[HttpIO] = SupabaseAuthAdminOAuth(
            self.executor, self.base_url, default_headers
        )
        self.custom_providers: SupabaseAuthAdminCustomProviders[HttpIO] = (
            SupabaseAuthAdminCustomProviders(
                self.executor, self.base_url, default_headers
            )
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
            query=_redirect_to_as_query(redirect_to),
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
            query=_redirect_to_as_query(params.redirect_to),
        )

        return parse_link_response(response)

    @handle_http_io
    def sign_out(self, jwt: str, scope: SignOutScope = "global") -> HttpMethod[None]:
        """
        Signs out the user the access token `jwt` belongs to. `scope` picks
        which of their sessions end: `"global"` ends all of them, `"local"`
        ends only the session of `jwt`, and `"others"` ends every session
        except the one of `jwt`.

        `jwt` must not have expired. An answer that the user is already gone
        counts as success, and so does one that the session is already gone
        for `"local"`. An access token stays valid until it expires, since
        only refresh tokens can be revoked.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        _check_sign_out_scope(scope)
        yield from _logout(jwt, scope)

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
    ) -> HttpMethod[UserList]:
        """
        Get a page of users, together with the next page, the last page and
        the total number of users.

        Use `iter_users` on the sync client or `aiter_users` on the async
        client to go through every user without handling pages.

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
        return _validate_paginated_model(response, UserList)

    @handle_http_io
    def get_user_by_id(self, user_id: str) -> HttpMethod[UserResponse]:
        """
        Get user by id.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        validate_uuid(user_id)

        response = yield EmptyRequest(
            method="GET",
            path=["admin", "users", user_id],
        )
        return parse_user_response(response)

    @handle_http_io
    def update_user_by_id(
        self,
        user_id: str,
        attributes: AdminUserAttributes,
    ) -> HttpMethod[UserResponse]:
        """
        Updates the user data.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        validate_uuid(user_id)
        response = yield JSONRequest(
            method="PUT",
            path=["admin", "users", user_id],
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
            raise _handle_error_response(response)


class SyncSupabaseAuthAdmin(SupabaseAuthAdmin[SyncHttpIO]):
    def __init__(
        self,
        url: str,
        http_session: HttpSession,
        default_headers: dict[str, str] | None = None,
        *,
        request_timeout: float | None = None,
        retry: RetryPolicy | None = None,
    ) -> None:
        super().__init__(
            executor=SyncHttpIO(
                session=http_session, request_timeout=request_timeout, retry=retry
            ),
            base_url=URL(url),
            default_headers=Headers.from_mapping(default_headers)
            if default_headers
            else Headers.empty(),
        )

    def iter_users(self, per_page: int | None = None) -> Iterator[User]:
        """
        Iterate over every user, fetching one page at a time as the iteration
        reaches it. Pages are numbered, so users created or deleted while
        iterating can shift the pages and be skipped or returned twice.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        page: int | None = 1
        while page is not None:
            result = self.list_users(page=page, per_page=per_page)
            yield from result.users
            next_page = result.next_page
            page = (
                next_page if result.users and next_page and next_page > page else None
            )

    def __enter__(self) -> Self:
        self.executor.session.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.executor.session.__exit__(exc_type, exc, tb)


class AsyncSupabaseAuthAdmin(SupabaseAuthAdmin[AsyncHttpIO]):
    def __init__(
        self,
        url: str,
        http_session: AsyncHttpSession,
        default_headers: dict[str, str] | None = None,
        *,
        request_timeout: float | None = None,
        retry: RetryPolicy | None = None,
    ) -> None:
        super().__init__(
            executor=AsyncHttpIO(
                session=http_session, request_timeout=request_timeout, retry=retry
            ),
            base_url=URL(url),
            default_headers=Headers.from_mapping(default_headers)
            if default_headers
            else Headers.empty(),
        )

    async def aiter_users(self, per_page: int | None = None) -> AsyncIterator[User]:
        """
        Iterate over every user, fetching one page at a time as the iteration
        reaches it. Pages are numbered, so users created or deleted while
        iterating can shift the pages and be skipped or returned twice.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.
        """
        page: int | None = 1
        while page is not None:
            result = await self.list_users(page=page, per_page=per_page)
            for user in result.users:
                yield user
            next_page = result.next_page
            page = (
                next_page if result.users and next_page and next_page > page else None
            )

    async def __aenter__(self) -> Self:
        await self.executor.session.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.executor.session.__aexit__(exc_type, exc, tb)
