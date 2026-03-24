from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal

from pydantic import BaseModel, TypeAdapter

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

    def get_error_message(self) -> str:
        return (
            self.msg
            or self.message
            or self.error_description
            or self.error
            or "Unknown"
        )


class UserDoesntExist(Exception):
    def __init__(self, access_token: str) -> None:
        self.access_token = access_token


@dataclass
class AuthError(Exception):
    message: str
    code: ErrorCode | None


@dataclass
class AuthApiError(AuthError):
    status: int


@dataclass
class AuthUnknownError(AuthError):
    data: bytes
    status: int


@dataclass
class CustomAuthError(AuthError):
    status: int


class AuthSessionMissingError(CustomAuthError):
    def __init__(self) -> None:
        CustomAuthError.__init__(
            self,
            message="Auth session missing!",
            status=400,
            code=None,
        )


class AuthInvalidCredentialsError(CustomAuthError):
    def __init__(self, message: str) -> None:
        CustomAuthError.__init__(
            self,
            message=message,
            status=400,
            code=None,
        )


class AuthImplicitGrantRedirectError(CustomAuthError):
    def __init__(
        self,
        message: str,
        error: str | None = None,
        code: str | None = None,
    ) -> None:
        CustomAuthError.__init__(
            self,
            message=message,
            status=500,
            code=None,
        )
        self.detail_error = error
        self.detail_code = code


class AuthRetryableError(CustomAuthError):
    def __init__(self, message: str, status: int) -> None:
        CustomAuthError.__init__(
            self,
            message,
            status=status,
            code=None,
        )


class AuthWeakPasswordError(CustomAuthError):
    def __init__(self, message: str, status: int, reasons: List[str]) -> None:
        CustomAuthError.__init__(
            self,
            message=message,
            status=status,
            code="weak_password",
        )
        self.reasons = reasons


class AuthInvalidJwtError(CustomAuthError):
    def __init__(self, message: str) -> None:
        CustomAuthError.__init__(
            self,
            message=message,
            status=400,
            code="invalid_jwt",
        )
