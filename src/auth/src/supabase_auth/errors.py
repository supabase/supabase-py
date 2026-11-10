from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ValidationError, field_validator
from supabase_utils.errors import SupabaseError
from supabase_utils.http.errors import SupabaseAPIError

if TYPE_CHECKING:
    from supabase_utils.http.request import Response


class ErrorCode(StrEnum):
    """The error codes the auth service names a failure with, see
    https://supabase.com/docs/guides/auth/debugging/error-codes.

    `AuthError.code` is a member when the code is known to this version of
    the SDK, and the plain string the service sent otherwise.
    """

    UNEXPECTED_FAILURE = "unexpected_failure"
    VALIDATION_FAILED = "validation_failed"
    BAD_JSON = "bad_json"
    EMAIL_EXISTS = "email_exists"
    PHONE_EXISTS = "phone_exists"
    BAD_JWT = "bad_jwt"
    NOT_ADMIN = "not_admin"
    NO_AUTHORIZATION = "no_authorization"
    USER_NOT_FOUND = "user_not_found"
    SESSION_NOT_FOUND = "session_not_found"
    SESSION_EXPIRED = "session_expired"
    REFRESH_TOKEN_NOT_FOUND = "refresh_token_not_found"
    REFRESH_TOKEN_ALREADY_USED = "refresh_token_already_used"
    FLOW_STATE_NOT_FOUND = "flow_state_not_found"
    FLOW_STATE_EXPIRED = "flow_state_expired"
    SIGNUP_DISABLED = "signup_disabled"
    USER_BANNED = "user_banned"
    PROVIDER_EMAIL_NEEDS_VERIFICATION = "provider_email_needs_verification"
    INVITE_NOT_FOUND = "invite_not_found"
    BAD_OAUTH_STATE = "bad_oauth_state"
    BAD_OAUTH_CALLBACK = "bad_oauth_callback"
    OAUTH_PROVIDER_NOT_SUPPORTED = "oauth_provider_not_supported"
    UNEXPECTED_AUDIENCE = "unexpected_audience"
    SINGLE_IDENTITY_NOT_DELETABLE = "single_identity_not_deletable"
    EMAIL_CONFLICT_IDENTITY_NOT_DELETABLE = "email_conflict_identity_not_deletable"
    IDENTITY_ALREADY_EXISTS = "identity_already_exists"
    EMAIL_PROVIDER_DISABLED = "email_provider_disabled"
    PHONE_PROVIDER_DISABLED = "phone_provider_disabled"
    TOO_MANY_ENROLLED_MFA_FACTORS = "too_many_enrolled_mfa_factors"
    MFA_FACTOR_NAME_CONFLICT = "mfa_factor_name_conflict"
    MFA_FACTOR_NOT_FOUND = "mfa_factor_not_found"
    MFA_IP_ADDRESS_MISMATCH = "mfa_ip_address_mismatch"
    MFA_CHALLENGE_EXPIRED = "mfa_challenge_expired"
    MFA_VERIFICATION_FAILED = "mfa_verification_failed"
    MFA_VERIFICATION_REJECTED = "mfa_verification_rejected"
    INSUFFICIENT_AAL = "insufficient_aal"
    CAPTCHA_FAILED = "captcha_failed"
    SAML_PROVIDER_DISABLED = "saml_provider_disabled"
    MANUAL_LINKING_DISABLED = "manual_linking_disabled"
    SMS_SEND_FAILED = "sms_send_failed"
    EMAIL_NOT_CONFIRMED = "email_not_confirmed"
    PHONE_NOT_CONFIRMED = "phone_not_confirmed"
    REAUTH_NONCE_MISSING = "reauth_nonce_missing"
    SAML_RELAY_STATE_NOT_FOUND = "saml_relay_state_not_found"
    SAML_RELAY_STATE_EXPIRED = "saml_relay_state_expired"
    SAML_IDP_NOT_FOUND = "saml_idp_not_found"
    SAML_ASSERTION_NO_USER_ID = "saml_assertion_no_user_id"
    SAML_ASSERTION_NO_EMAIL = "saml_assertion_no_email"
    USER_ALREADY_EXISTS = "user_already_exists"
    SSO_PROVIDER_NOT_FOUND = "sso_provider_not_found"
    SAML_METADATA_FETCH_FAILED = "saml_metadata_fetch_failed"
    SAML_IDP_ALREADY_EXISTS = "saml_idp_already_exists"
    SSO_DOMAIN_ALREADY_EXISTS = "sso_domain_already_exists"
    SAML_ENTITY_ID_MISMATCH = "saml_entity_id_mismatch"
    CONFLICT = "conflict"
    PROVIDER_DISABLED = "provider_disabled"
    USER_SSO_MANAGED = "user_sso_managed"
    REAUTHENTICATION_NEEDED = "reauthentication_needed"
    SAME_PASSWORD = "same_password"
    REAUTHENTICATION_NOT_VALID = "reauthentication_not_valid"
    OTP_EXPIRED = "otp_expired"
    OTP_DISABLED = "otp_disabled"
    IDENTITY_NOT_FOUND = "identity_not_found"
    WEAK_PASSWORD = "weak_password"
    OVER_REQUEST_RATE_LIMIT = "over_request_rate_limit"
    OVER_EMAIL_SEND_RATE_LIMIT = "over_email_send_rate_limit"
    OVER_SMS_SEND_RATE_LIMIT = "over_sms_send_rate_limit"
    BAD_CODE_VERIFIER = "bad_code_verifier"
    ANONYMOUS_PROVIDER_DISABLED = "anonymous_provider_disabled"
    HOOK_TIMEOUT = "hook_timeout"
    HOOK_TIMEOUT_AFTER_RETRY = "hook_timeout_after_retry"
    HOOK_PAYLOAD_OVER_SIZE_LIMIT = "hook_payload_over_size_limit"
    HOOK_PAYLOAD_INVALID_CONTENT_TYPE = "hook_payload_invalid_content_type"
    REQUEST_TIMEOUT = "request_timeout"
    MFA_PHONE_ENROLL_NOT_ENABLED = "mfa_phone_enroll_not_enabled"
    MFA_PHONE_VERIFY_NOT_ENABLED = "mfa_phone_verify_not_enabled"
    MFA_TOTP_ENROLL_NOT_ENABLED = "mfa_totp_enroll_not_enabled"
    MFA_TOTP_VERIFY_NOT_ENABLED = "mfa_totp_verify_not_enabled"
    MFA_WEBAUTHN_ENROLL_NOT_ENABLED = "mfa_webauthn_enroll_not_enabled"
    MFA_WEBAUTHN_VERIFY_NOT_ENABLED = "mfa_webauthn_verify_not_enabled"
    MFA_VERIFIED_FACTOR_EXISTS = "mfa_verified_factor_exists"
    INVALID_CREDENTIALS = "invalid_credentials"
    EMAIL_ADDRESS_NOT_AUTHORIZED = "email_address_not_authorized"
    EMAIL_ADDRESS_INVALID = "email_address_invalid"
    INVALID_JWT = "invalid_jwt"


class WeakPasswordReasons(BaseModel):
    reasons: list[str]


class RawApiError(BaseModel):
    msg: str | None = None
    message: str | None = None
    error: str | None = None
    code: int | None = None
    error_description: str | None = None
    error_code: str | None = None
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
    `code` is an `ErrorCode` when the service named the failure with a code
    this version of the SDK knows, and the plain string it sent otherwise.
    """


class AuthApiError(AuthError, SupabaseAPIError):
    """Raised when the auth service answered a request with an error."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        code: ErrorCode | str | None = None,
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
        code: ErrorCode | str | None = None,
        response: Response | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code, code=code, response=response)


class UserDoesNotExistError(AuthError):
    def __init__(self) -> None:
        super().__init__(
            "User does not exist for the provided access token",
            code=ErrorCode.USER_NOT_FOUND,
        )


class AuthSessionMissingError(AuthError):
    def __init__(self) -> None:
        super().__init__("Auth session missing!")


class AuthInvalidCredentialsError(AuthError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class AuthImplicitGrantRedirectError(AuthError):
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
    retrying: a rate limit (429) or a server or gateway error (5xx).

    A session refresh that fails with it keeps the session and is retried
    later, see `SignOutReason`."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        code: ErrorCode | str | None = None,
        response: Response | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code, code=code, response=response)


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
            message,
            status_code=status_code,
            code=ErrorCode.WEAK_PASSWORD,
            response=response,
        )
        self.reasons = reasons


class AuthInvalidJwtError(AuthError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code=ErrorCode.INVALID_JWT)
