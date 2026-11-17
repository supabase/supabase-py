from __future__ import annotations

from typing import TYPE_CHECKING, get_args

from supabase_utils.http.headers import Headers
from supabase_utils.http.query import URLQuery
from supabase_utils.http.request import EmptyRequest

from .errors import AuthApiError, AuthError, ErrorCode
from .helpers import _handle_error_response
from .types import SignOutScope

if TYPE_CHECKING:
    from supabase_utils.http.io import HttpMethod

_SESSION_GONE_ON_REFRESH = frozenset(
    {
        ErrorCode.REFRESH_TOKEN_NOT_FOUND,
        ErrorCode.SESSION_NOT_FOUND,
        ErrorCode.SESSION_EXPIRED,
    }
)


_SIGN_OUT_SCOPES: tuple[str, ...] = get_args(SignOutScope)


def _check_sign_out_scope(scope: str) -> None:
    if scope not in _SIGN_OUT_SCOPES:
        raise ValueError(
            f"Invalid sign out scope {scope!r}, expected one of {_SIGN_OUT_SCOPES}"
        )


def _is_already_signed_out(error: AuthError, scope: SignOutScope) -> bool:
    """Whether a logout answer means nothing is left to revoke for `scope`.
    A gone user has no sessions left, and a gone current session is all that
    `local` revokes."""
    if not isinstance(error, AuthApiError) or error.status_code != 403:
        return False
    return error.code == ErrorCode.USER_NOT_FOUND or (
        scope == "local" and error.code == ErrorCode.SESSION_NOT_FOUND
    )


def _is_session_gone(error: Exception) -> bool:
    """Whether a failed refresh means the session can never be refreshed
    again, so nothing is left to revoke for `local`."""
    return (
        isinstance(error, AuthApiError)
        and error.status_code == 400
        and error.code in _SESSION_GONE_ON_REFRESH
    )


def _logout(access_token: str, scope: SignOutScope) -> HttpMethod[None]:
    response = yield EmptyRequest(
        method="POST",
        path=["logout"],
        query=URLQuery.from_mapping({"scope": scope}),
        headers=Headers.from_mapping({"Authorization": f"Bearer {access_token}"}),
    )
    if response.is_success:
        return
    error = _handle_error_response(response)
    if not _is_already_signed_out(error, scope):
        raise error
