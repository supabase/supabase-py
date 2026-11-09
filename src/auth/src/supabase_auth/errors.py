from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, TypeAdapter, ValidationError, field_validator
from supabase_utils.errors import SupabaseError
from supabase_utils.http.errors import SupabaseAPIError

if TYPE_CHECKING:
    from supabase_utils.http.request import Response

ErrorCode = Literal[
    "unexpected_failure",
    "validation_failed",
    "bad_json",
    "email_exists",
    "phone_exists",
    "bad_jwt",
    "not_admin",
    "no_authorization",
    "user_not_found",
    "session_not_found",
    "flow_state_not_found",
    "flow_state_expired",
    "signup_disabled",
    "user_banned",
    "provider_email_needs_verification",
    "invite_not_found",
    "bad_oauth_state",
    "bad_oauth_callback",
    "oauth_provider_not_supported",
    "unexpected_audience",
    "single_identity_not_deletable",
    "email_conflict_identity_not_deletable",
    "identity_already_exists",
    "email_provider_disabled",
    "phone_provider_disabled",
    "too_many_enrolled_mfa_factors",
    "mfa_factor_name_conflict",
    "mfa_factor_not_found",
    "mfa_ip_address_mismatch",
    "mfa_challenge_expired",
    "mfa_verification_failed",
    "mfa_verification_rejected",
    "insufficient_aal",
    "captcha_failed",
    "saml_provider_disabled",
    "manual_linking_disabled",
    "sms_send_failed",
    "email_not_confirmed",
    "phone_not_confirmed",
    "reauth_nonce_missing",
    "saml_relay_state_not_found",
    "saml_relay_state_expired",
    "saml_idp_not_found",
    "saml_assertion_no_user_id",
    "saml_assertion_no_email",
    "user_already_exists",
    "sso_provider_not_found",
    "saml_metadata_fetch_failed",
    "saml_idp_already_exists",
    "sso_domain_already_exists",
    "saml_entity_id_mismatch",
    "conflict",
    "provider_disabled",
    "user_sso_managed",
    "reauthentication_needed",
    "same_password",
    "reauthentication_not_valid",
    "otp_expired",
    "otp_disabled",
    "identity_not_found",
    "weak_password",
    "over_request_rate_limit",
    "over_email_send_rate_limit",
    "over_sms_send_rate_limit",
    "bad_code_verifier",
    "anonymous_provider_disabled",
    "hook_timeout",
    "hook_timeout_after_retry",
    "hook_payload_over_size_limit",
    "hook_payload_invalid_content_type",
    "request_timeout",
    "mfa_phone_enroll_not_enabled",
    "mfa_phone_verify_not_enabled",
    "mfa_totp_enroll_not_enabled",
    "mfa_totp_verify_not_enabled",
    "mfa_webauthn_enroll_not_enabled",
    "mfa_webauthn_verify_not_enabled",
    "mfa_verified_factor_exists",
    "invalid_credentials",
    "email_address_not_authorized",
    "email_address_invalid",
    "invalid_jwt",
]

ErrorCodeAdapter: TypeAdapter[ErrorCode] = TypeAdapter(ErrorCode)


class WeakPasswordReasons(BaseModel):
    reasons: list[str]


class RawApiError(BaseModel):
    msg: str | None = None
    message: str | None = None
    error: str | None = None
    code: int | None = None
    error_description: str | None = None
    error_code: ErrorCode | None = None
    weak_password: WeakPasswordReasons | None = None

    @field_validator("weak_password", mode="before")
    @classmethod
    def _ignore_malformed_weak_password(cls, value: Any) -> WeakPasswordReasons | None:
        try:
            return WeakPasswordReasons.model_validate(value)
        except ValidationError:
            return None

    def get_error_message(self) -> str:
        return (
            self.msg
            or self.message
            or self.error_description
            or self.error
            or "Unknown"
        )


class AuthError(SupabaseError):
    """Raised when an auth operation fails.

    A plain `AuthError` is a failure the client raised on its own, such as a
    missing session. A failure the auth service reported is an `AuthApiError`.
    `code` is one of `ErrorCode` when the service named the failure, see
    https://supabase.com/docs/guides/auth/debugging/error-codes.
    """


class AuthApiError(AuthError, SupabaseAPIError):
    """Raised when the auth service answered a request with an error."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        code: ErrorCode | None = None,
        response: Response | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code, code=code, response=response)


class AuthUnknownError(AuthError, SupabaseAPIError):
    """Raised when the auth service answered with an error that could not be
    parsed. The body is `response.content`."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        code: ErrorCode | None = None,
        response: Response | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code, code=code, response=response)


class CustomAuthError(AuthError):
    """Base class of the errors the auth client raises on its own, without a
    response from the auth service."""

    def __init__(self, message: str, *, code: ErrorCode | None = None) -> None:
        super().__init__(message, code=code)


class UserDoesNotExistError(CustomAuthError):
    def __init__(self) -> None:
        super().__init__(
            "User does not exist for the provided access token",
            code="user_not_found",
        )


class AuthSessionMissingError(CustomAuthError):
    def __init__(self) -> None:
        super().__init__("Auth session missing!")


class AuthInvalidCredentialsError(CustomAuthError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class AuthImplicitGrantRedirectError(CustomAuthError):
    def __init__(
        self,
        message: str,
        error: str | None = None,
        code: str | None = None,
    ) -> None:
        super().__init__(message)
        self.detail_error = error
        self.detail_code = code


class AuthRetryableError(AuthApiError):
    """Raised when the auth service answered with a status that is worth
    retrying, such as a gateway error."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        response: Response | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code, response=response)


class AuthWeakPasswordError(AuthApiError):
    """Raised when the auth service rejected a password. `reasons` lists what
    it lacked."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        reasons: list[str],
        response: Response | None = None,
    ) -> None:
        super().__init__(
            message, status_code=status_code, code="weak_password", response=response
        )
        self.reasons = reasons


class AuthInvalidJwtError(CustomAuthError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="invalid_jwt")
