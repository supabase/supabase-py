from __future__ import annotations

import base64
import hashlib
import secrets
import string
import uuid
from base64 import urlsafe_b64decode
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal
from urllib.parse import parse_qsl, urlparse, urlsplit

from cryptography.exceptions import UnsupportedAlgorithm
from jwt import PyJWK
from jwt.exceptions import PyJWTError
from pydantic import BaseModel, TypeAdapter, ValidationError
from supabase_utils.http.query import URLQuery

from .errors import (
    AuthApiError,
    AuthError,
    AuthInvalidJwtError,
    AuthRetryableError,
    AuthUnknownError,
    AuthWeakPasswordError,
    ErrorCode,
    RawApiError,
)
from .types import (
    JWK,
    AuthChangeEvent,
    AuthOtpResponse,
    AuthResponse,
    GenerateLinkProperties,
    GenerateLinkResponse,
    JWKSet,
    JWTHeader,
    JWTPayload,
    LinkIdentityResponse,
    Pagination,
    Session,
    SSOResponse,
    User,
    UserResponse,
    VerifyOtpParams,
)

if TYPE_CHECKING:
    from supabase_utils.http.request import Response


def parse_auth_response(response: Response) -> AuthResponse:
    try:
        session = _validate_model(response, Session)
        user = session.user
    except ValidationError:
        session = None
        user = _validate_model(response, User)
    return AuthResponse(user=user, session=session)


class _PendingSecureEmailChange(BaseModel):
    """What auth answers to the first of the two confirmations of a secure
    email change. It issues no session until the other address confirms too.
    It sends the status as a string today, so a number is accepted too in
    case that changes."""

    code: Literal["200", 200]
    msg: str


def _parse_verify_otp_response(
    response: Response, params: VerifyOtpParams
) -> AuthResponse:
    if params.body.type == "email_change" and response.is_success:
        try:
            _PendingSecureEmailChange.model_validate_json(response.content)
        except ValidationError:
            pass
        else:
            return AuthResponse()
    return parse_auth_response(response)


def _verify_otp_event(params: VerifyOtpParams) -> AuthChangeEvent:
    if params.body.type == "recovery":
        return AuthChangeEvent.PASSWORD_RECOVERY
    return AuthChangeEvent.SIGNED_IN


def parse_auth_otp_response(response: Response) -> AuthOtpResponse:
    return _validate_model(response, AuthOtpResponse)


def parse_link_identity_response(response: Response) -> LinkIdentityResponse:
    return _validate_model(response, LinkIdentityResponse)


def parse_link_response(response: Response) -> GenerateLinkResponse:
    properties = _validate_model(response, GenerateLinkProperties)
    user = _validate_model(response, User)
    return GenerateLinkResponse(properties=properties, user=user)


UserParser: TypeAdapter[UserResponse | User] = TypeAdapter(UserResponse | User)


def parse_user_response(response: Response) -> UserResponse:
    if response.is_success:
        parsed = UserParser.validate_json(response.content)
        return UserResponse(user=parsed) if isinstance(parsed, User) else parsed
    raise _handle_error_response(response)


def parse_sso_response(response: Response) -> SSOResponse:
    return _validate_model(response, SSOResponse)


def parse_jwks(response: Response) -> JWKSet:
    return _validate_model(response, JWKSet)


def _validate_model[Model: BaseModel](response: Response, model: type[Model]) -> Model:
    if response.is_success:
        return model.model_validate_json(response.content)
    raise _handle_error_response(response)


def _validate_paginated_model[Model: Pagination](
    response: Response, model: type[Model]
) -> Model:
    result = _validate_model(response, model)
    total = (response.headers.get("x-total-count") or "").strip()
    if total.isdigit():
        result.total = int(total)
    for link in (response.headers.get("link") or "").split(","):
        target, _, parameters = link.partition(";")
        query = dict(parse_qsl(urlsplit(target.strip().strip("<>")).query))
        page = query.get("page", "")
        if not page.isdigit():
            continue
        for parameter in parameters.split(";"):
            key, _, value = parameter.partition("=")
            if key.strip() != "rel":
                continue
            rel = value.strip().strip('"')
            if rel == "next":
                result.next_page = int(page)
            elif rel == "last":
                result.last_page = int(page)
    return result


def _validate_adapter[Inner](response: Response, adapter: TypeAdapter[Inner]) -> Inner:
    if response.is_success:
        return adapter.validate_json(response.content)
    raise _handle_error_response(response)


def _parse_error_code(value: str | None) -> ErrorCode | str | None:
    """The `ErrorCode` for `value`, or `value` itself when this version of
    the SDK does not know the code."""
    if value is None:
        return None
    try:
        return ErrorCode(value)
    except ValueError:
        return value


def _is_retryable_status(status: int) -> bool:
    """A rate limit or a server or gateway error says nothing about the
    request itself, so the same request may succeed later."""
    return status == 429 or status >= 500


def _handle_error_response(response: Response) -> AuthError:
    try:
        raw_error = RawApiError.model_validate_json(response.content)
    except ValidationError:
        # A gateway or rate limiter answers with its own page, not with an
        # auth error. The status still says the request may succeed later.
        if _is_retryable_status(response.status):
            return AuthRetryableError(
                "Unexpected error: Unable to parse API error",
                status_code=response.status,
                code=ErrorCode.UNEXPECTED_FAILURE,
                response=response,
            )
        return AuthUnknownError(
            "Unexpected error: Unable to parse API error",
            status_code=response.status,
            code=ErrorCode.UNEXPECTED_FAILURE,
            response=response,
        )
    error_code = _parse_error_code(raw_error.error_code)
    if not response.is_error or _is_retryable_status(response.status):
        return AuthRetryableError(
            raw_error.get_error_message(),
            status_code=response.status,
            code=error_code,
            response=response,
        )

    if (
        error_code is None
        and raw_error.weak_password
        and raw_error.weak_password.reasons
    ):
        return AuthWeakPasswordError(
            raw_error.get_error_message(),
            status_code=response.status,
            reasons=raw_error.weak_password.reasons,
            response=response,
        )
    if error_code is ErrorCode.WEAK_PASSWORD:
        return AuthWeakPasswordError(
            raw_error.get_error_message(),
            status_code=response.status,
            reasons=raw_error.weak_password.reasons if raw_error.weak_password else [],
            response=response,
        )

    return AuthApiError(
        raw_error.get_error_message(),
        status_code=response.status or 500,
        code=error_code,
        response=response,
    )


def _str_from_base64url(base64url: str) -> str:
    # Addding padding otherwise the following error happens:
    # binascii.Error: Incorrect padding
    base64url_with_padding = base64url + "=" * (-len(base64url) % 4)
    return urlsafe_b64decode(base64url_with_padding).decode("utf-8")


def base64url_to_bytes(base64url: str) -> bytes:
    # Addding padding otherwise the following error happens:
    # binascii.Error: Incorrect padding
    base64url_with_padding = base64url + "=" * (-len(base64url) % 4)
    return urlsafe_b64decode(base64url_with_padding)


@dataclass
class DecodedJWT:
    header: JWTHeader
    payload: JWTPayload
    signature: bytes
    raw_header: str
    raw_payload: str


def decode_jwt(token: str) -> DecodedJWT:
    parts = token.split(".")
    if len(parts) != 3:
        raise AuthInvalidJwtError("Invalid JWT structure")

    try:
        header = JWTHeader.model_validate_json(base64url_to_bytes(parts[0]))
        payload = JWTPayload.model_validate_json(base64url_to_bytes(parts[1]))
        signature = base64url_to_bytes(parts[2])
    except ValueError as e:
        raise AuthInvalidJwtError("Invalid JWT structure") from e

    return DecodedJWT(
        header=header,
        payload=payload,
        signature=signature,
        raw_header=parts[0],
        raw_payload=parts[1],
    )


def generate_pkce_verifier(length: int = 64) -> str:
    """Generate a random PKCE verifier of the specified length."""
    if length < 43 or length > 128:
        raise ValueError("PKCE verifier length must be between 43 and 128 characters")

    # Define characters that can be used in the PKCE verifier
    charset = string.ascii_letters + string.digits + "-._~"

    return "".join(secrets.choice(charset) for _ in range(length))


def generate_pkce_challenge(code_verifier: str) -> str:
    """Generate a code challenge from a PKCE verifier."""
    # Hash the verifier using SHA-256
    verifier_bytes = code_verifier.encode("utf-8")
    sha256_hash = hashlib.sha256(verifier_bytes).digest()

    return base64.urlsafe_b64encode(sha256_hash).rstrip(b"=").decode("utf-8")


def is_http_url(url: str) -> bool:
    return urlparse(url).scheme in {"https", "http"}


def validate_expiration(expires_at: int | None) -> None:
    if not expires_at:
        raise AuthInvalidJwtError("JWT has no expiration time")

    time_now = datetime.now(UTC).timestamp()
    if expires_at <= time_now:
        raise AuthInvalidJwtError("JWT has expired")


def _validate_not_before(not_before: float | None) -> None:
    if not_before is not None and not_before > datetime.now(UTC).timestamp():
        raise AuthInvalidJwtError("JWT is not yet valid")


_LOCALLY_VERIFIABLE_ALGORITHMS = frozenset(
    {"RS256", "ES256", "EdDSA", "Ed25519", "Ed448"}
)
_EDDSA_CURVES = frozenset({"Ed25519", "Ed448"})


def _is_locally_verifiable(header_alg: str | None) -> bool:
    """Whether a token with this header `alg` can be verified against the JWK
    Set rather than by the server."""
    return header_alg in _LOCALLY_VERIFIABLE_ALGORITHMS


def _bind_algorithm(jwk: JWK) -> str | None:
    """The algorithm the JWK verifies, taken from the key and never from the
    token header, or `None` when this SDK cannot verify with it. EdDSA keys
    bind to their curve, `Ed25519` or `Ed448`."""
    match jwk.kty, jwk.crv, jwk.alg:
        case "RSA", _, None | "RS256":
            return "RS256"
        case "EC", "P-256", None | "ES256":
            return "ES256"
        case "OKP", "Ed25519" | "Ed448" as curve, None | "EdDSA":
            return curve
        case "OKP", "Ed25519" | "Ed448" as curve, alg if alg == curve:
            return curve
        case _:
            return None


def _header_names_algorithm(header_alg: str | None, bound: str) -> bool:
    if header_alg == bound:
        return True
    return header_alg == "EdDSA" and bound in _EDDSA_CURVES


def _verify_signature(decoded: DecodedJWT, jwk: JWK, bound: str) -> bool | None:
    """Checks the token signature with the JWK, or returns `None` when the
    runtime cannot import the key or perform the algorithm."""
    key_data = jwk.model_dump(exclude_none=True, exclude={"alg", "key_ops"})
    algorithm = "EdDSA" if bound in _EDDSA_CURVES else bound
    try:
        key = PyJWK(key_data, algorithm)
    except (PyJWTError, UnsupportedAlgorithm):
        return None
    signing_input = f"{decoded.raw_header}.{decoded.raw_payload}".encode()
    try:
        return key.Algorithm.verify(signing_input, key.key, decoded.signature)
    except UnsupportedAlgorithm:
        return None


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


def _redirect_to_as_query(redirect_to: str | None) -> URLQuery:
    if redirect_to:
        return URLQuery.from_mapping({"redirect_to": redirect_to})
    return URLQuery.empty()


def _parse_url_params(url: str) -> dict[str, str]:
    """The implicit grant returns its tokens in the fragment; a query string
    parameter wins over the fragment, as in supabase-js."""
    parts = urlsplit(url)
    params = dict(parse_qsl(parts.fragment))
    params.update(parse_qsl(parts.query))
    return params


def _is_implicit_grant_flow(url: str) -> bool:
    params = _parse_url_params(url)
    return "access_token" in params or "error_description" in params


_JWKS_REFETCH_MIN_WAIT = 1.0
_JWKS_REFETCH_MAX_WAIT = 16.0


def _jwk_by_kid(jwks: JWKSet, kid: str) -> JWK | None:
    return next((jwk for jwk in jwks.keys if jwk.kid == kid), None)
