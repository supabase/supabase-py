from __future__ import annotations

import base64
import hashlib
import re
import secrets
import string
import uuid
from base64 import urlsafe_b64decode
from datetime import datetime
from typing import Any, TypedDict
from urllib.parse import parse_qs, urlparse

from httpx import HTTPStatusError, RequestError, Response
from pydantic import TypeAdapter, ValidationError

from .constants import (
    API_VERSION_HEADER_NAME,
    API_VERSIONS_2024_01_01_TIMESTAMP,
)
from .errors import (
    AuthApiError,
    AuthError,
    AuthInvalidJwtError,
    AuthRetryableError,
    AuthUnknownError,
    AuthWeakPasswordError,
)
from .types import (
    AuthOtpResponse,
    AuthResponse,
    GenerateLinkProperties,
    GenerateLinkResponse,
    JWKSet,
    JWTHeader,
    JWTPayload,
    LinkIdentityResponse,
    Session,
    SSOResponse,
    User,
    UserResponse,
)


def parse_auth_response(response: Response) -> AuthResponse:
    try:
        session = Session.model_validate_json(response.content)
        user = session.user
    except ValidationError:
        session = None
        user = User.model_validate_json(response.content)
    return AuthResponse(user=user, session=session)


def parse_auth_otp_response(response: Response) -> AuthOtpResponse:
    return AuthOtpResponse.model_validate_json(response.content)


def parse_link_identity_response(response: Response) -> LinkIdentityResponse:
    return LinkIdentityResponse.model_validate_json(response.content)


def parse_link_response(response: Response) -> GenerateLinkResponse:
    properties = GenerateLinkProperties.model_validate_json(response.content)
    user = User.model_validate_json(response.content)
    return GenerateLinkResponse(properties=properties, user=user)


UserParser: TypeAdapter = TypeAdapter(UserResponse | User)


def parse_user_response(response: Response) -> UserResponse:
    parsed = UserParser.validate_json(response.content)
    return UserResponse(user=parsed) if isinstance(parsed, User) else parsed


def parse_sso_response(response: Response) -> SSOResponse:
    return SSOResponse.model_validate_json(response.content)


JWKSetParser: TypeAdapter[JWKSet] = TypeAdapter(JWKSet)


def _parse_url_params(url: str) -> dict[str, list[str]]:
    result = urlparse(url)
    return {**parse_qs(result.fragment), **parse_qs(result.query)}


def parse_jwks(response: Response) -> JWKSet:
    jwk = JWKSetParser.validate_json(response.content)
    if len(jwk["keys"]) == 0:
        raise AuthInvalidJwtError("JWKS is empty")

    return jwk


def get_error_message(error: Any) -> str:
    props = ["msg", "message", "error_description", "error"]

    def filter(prop) -> bool:
        return prop in error if isinstance(error, dict) else hasattr(error, prop)

    return next((error[prop] for prop in props if filter(prop)), str(error))


def handle_exception(
    error: HTTPStatusError | RequestError | RuntimeError,
) -> AuthError:
    if not isinstance(error, HTTPStatusError):
        return AuthRetryableError(get_error_message(error), 0)
    try:
        network_error_codes = [502, 503, 504, 520, 521, 522, 523, 524, 530]
        status = error.response.status_code
        try:
            data = error.response.json()
        except Exception:
            if status in network_error_codes:
                # The reason phrase is empty when the server sends none and
                # the status is non-standard (e.g. Cloudflare's 520-530).
                return AuthRetryableError(
                    error.response.reason_phrase or f"HTTP {status}", status
                )
            raise
        if status in network_error_codes:
            return AuthRetryableError(get_error_message(data), status)

        error_code = None
        response_api_version = parse_response_api_version(error.response)

        if (
            response_api_version
            and (
                datetime.timestamp(response_api_version)
                >= API_VERSIONS_2024_01_01_TIMESTAMP
            )
            and isinstance(data, dict)
            and data
            and isinstance(data.get("code"), str)
        ):
            error_code = data.get("code")
        elif (
            isinstance(data, dict) and data and isinstance(data.get("error_code"), str)
        ):
            error_code = data.get("error_code")

        if error_code is None:
            # Legacy support for weak password errors, from before error codes
            # existed: the reasons are only carried by the `weak_password` object.
            weak_password = (
                data.get("weak_password") if isinstance(data, dict) else None
            )
            reasons = (
                weak_password.get("reasons")
                if isinstance(weak_password, dict)
                else None
            )
            if (
                isinstance(reasons, list)
                and reasons
                and all(isinstance(reason, str) for reason in reasons)
            ):
                return AuthWeakPasswordError(
                    get_error_message(data),
                    error.response.status_code,
                    reasons,
                )
        elif error_code == "weak_password":
            return AuthWeakPasswordError(
                get_error_message(data),
                error.response.status_code,
                data["weak_password"].get("reasons", {}),
            )

        return AuthApiError(
            get_error_message(data),
            error.response.status_code or 500,
            error_code,
        )
    except Exception as e:
        return AuthUnknownError(get_error_message(error), e)


def base64url_to_bytes(base64url: str) -> bytes:
    # Addding padding otherwise the following error happens:
    # binascii.Error: Incorrect padding
    base64url_with_padding = base64url + "=" * (-len(base64url) % 4)
    return urlsafe_b64decode(base64url_with_padding)


class DecodedJWT(TypedDict):
    header: JWTHeader
    payload: JWTPayload
    signature: bytes
    raw: dict[str, str]


JWTHeaderParser: TypeAdapter[JWTHeader] = TypeAdapter(JWTHeader)
JWTPayloadParser: TypeAdapter[JWTPayload] = TypeAdapter(JWTPayload)


def decode_jwt(token: str) -> DecodedJWT:
    parts = token.split(".")
    if len(parts) != 3:
        raise AuthInvalidJwtError("Invalid JWT structure")

    try:
        header = JWTHeaderParser.validate_json(base64url_to_bytes(parts[0]))
        payload = JWTPayloadParser.validate_json(base64url_to_bytes(parts[1]))
        signature = base64url_to_bytes(parts[2])
    except ValueError as e:
        raise AuthInvalidJwtError("Invalid JWT structure") from e

    return DecodedJWT(
        header=header,
        payload=payload,
        signature=signature,
        raw={
            "header": parts[0],
            "payload": parts[1],
        },
    )


def generate_pkce_verifier(length=64) -> str:
    """Generate a random PKCE verifier of the specified length."""
    if length < 43 or length > 128:
        raise ValueError("PKCE verifier length must be between 43 and 128 characters")

    # Define characters that can be used in the PKCE verifier
    charset = string.ascii_letters + string.digits + "-._~"

    return "".join(secrets.choice(charset) for _ in range(length))


def generate_pkce_challenge(code_verifier) -> str:
    """Generate a code challenge from a PKCE verifier."""
    # Hash the verifier using SHA-256
    verifier_bytes = code_verifier.encode("utf-8")
    sha256_hash = hashlib.sha256(verifier_bytes).digest()

    return base64.urlsafe_b64encode(sha256_hash).rstrip(b"=").decode("utf-8")


API_VERSION_REGEX = r"^2[0-9]{3}-(0[1-9]|1[0-2])-(0[1-9]|1[0-9]|2[0-9]|3[0-1])$"


def parse_response_api_version(response: Response) -> datetime | None:
    api_version = response.headers.get(API_VERSION_HEADER_NAME)

    if not api_version:
        return None

    if re.search(API_VERSION_REGEX, api_version) is None:
        return None

    try:
        dt = datetime.strptime(api_version, "%Y-%m-%d")
        return dt
    except Exception:
        return None


def is_http_url(url: str) -> bool:
    return urlparse(url).scheme in {"https", "http"}


def validate_exp(exp: int | None) -> None:
    if not exp:
        raise AuthInvalidJwtError("JWT has no expiration time")

    time_now = datetime.now().timestamp()
    if exp <= time_now:
        raise AuthInvalidJwtError("JWT has expired")


def is_valid_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


def validate_uuid(id: str | None) -> None:
    if id is None:
        raise ValueError("Invalid id, id is None")
    if not is_valid_uuid(id):
        raise ValueError(f"Invalid id, '{id}' is not a valid uuid")
