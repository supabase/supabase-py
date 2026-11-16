from __future__ import annotations

from typing import get_args

from .errors import AuthApiError, AuthError, ErrorCode
from .types import SignOutScope

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
