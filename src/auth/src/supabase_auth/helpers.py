from __future__ import annotations

import base64
import binascii
import hashlib
import re
import secrets
import string
import uuid
from base64 import urlsafe_b64decode
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Type, TypeVar
from urllib.parse import urlparse

from httpx import QueryParams, Response
from pydantic import BaseModel, TypeAdapter, ValidationError

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
    ErrorCodeAdapter,
    RawApiError,
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

TBaseModel = TypeVar("TBaseModel", bound=BaseModel)


def model_validate(model: Type[TBaseModel], contents: str | bytes) -> TBaseModel:
    """Compatibility layer between pydantic 1 and 2 for parsing an instance
    of a BaseModel from varied"""
    try:
        # pydantic > 2
        return model.model_validate_json(contents)
    except AttributeError:
        # pydantic < 2
        return model.parse_raw(contents)


def model_dump(model: BaseModel) -> Dict[str, Any]:
    """Compatibility layer between pydantic 1 and 2 for dumping a model's contents as a dict"""
    try:
        # pydantic > 2
        return model.model_dump()
    except AttributeError:
        # pydantic < 2
        return model.dict()


def model_dump_json(model: BaseModel) -> str:
    """Compatibility layer between pydantic 1 and 2 for dumping a model's contents as json"""
    try:
        # pydantic > 2
        return model.model_dump_json()
    except AttributeError:
        # pydantic < 2
        return model.json()


def parse_auth_response(response: Response) -> AuthResponse:
    try:
        session = validate_model(response, Session)
        user = session.user
    except ValidationError:
        session = None
        user = validate_model(response, User)
    return AuthResponse(user=user, session=session)


def parse_auth_otp_response(response: Response) -> AuthOtpResponse:
    return validate_model(response, AuthOtpResponse)


def parse_link_identity_response(response: Response) -> LinkIdentityResponse:
    return validate_model(response, LinkIdentityResponse)


def parse_link_response(response: Response) -> GenerateLinkResponse:
    properties = validate_model(response, GenerateLinkProperties)
    user = validate_model(response, User)
    return GenerateLinkResponse(properties=properties, user=user)


UserParser: TypeAdapter[UserResponse | User] = TypeAdapter(UserResponse | User)


def parse_user_response(response: Response) -> UserResponse:
    if response.is_success:
        parsed = UserParser.validate_json(response.content)
        return UserResponse(user=parsed) if isinstance(parsed, User) else parsed
    else:
        raise handle_error_response(response)


def parse_sso_response(response: Response) -> SSOResponse:
    return model_validate(SSOResponse, response.content)


JWKSetParser = TypeAdapter(JWKSet)


def parse_jwks(response: Response) -> JWKSet:
    jwk = JWKSetParser.validate_json(response.content)
    if len(jwk.keys) == 0:
        raise AuthInvalidJwtError("JWKS is empty")

    return jwk


Model = TypeVar("Model", bound=BaseModel)


def validate_model(response: Response, model: type[Model]) -> Model:
    if response.is_success:
        return model.model_validate_json(response.content)
    else:
        print(response.content)
        raise handle_error_response(response)


def handle_error_response(response: Response) -> AuthError:
    try:
        raw_error = RawApiError.model_validate_json(response.content)
    except ValidationError:
        return AuthUnknownError(
            message="Unexpected error: Unable to parse API error",
            code="unexpected_failure",
            status=response.status_code,
            data=response.content,
        )
    if not response.is_error:
        return AuthRetryableError(raw_error.get_error_message(), response.status_code)
    if 502 <= response.status_code <= 504:
        return AuthRetryableError(raw_error.get_error_message(), response.status_code)
    error_code = None
    response_api_version = parse_response_api_version(response)

    if (
        response_api_version
        and datetime.timestamp(response_api_version)
        >= API_VERSIONS_2024_01_01_TIMESTAMP
    ):
        error_code = ErrorCodeAdapter.validate_python(raw_error.error_code)
    else:
        error_code = raw_error.error_code

    if error_code is None and raw_error.weak_password:
        return AuthWeakPasswordError(
            message=raw_error.get_error_message(),
            status=response.status_code,
            reasons=raw_error.weak_password.reasons,
        )
    elif error_code == "weak_password":
        return AuthWeakPasswordError(
            raw_error.get_error_message(),
            status=response.status_code,
            reasons=raw_error.weak_password.reasons if raw_error.weak_password else [],
        )

    return AuthApiError(
        raw_error.get_error_message(),
        status=response.status_code or 500,
        code=error_code,
    )


def str_from_base64url(base64url: str) -> str:
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
        header = base64url_to_bytes(parts[0])
        payload = base64url_to_bytes(parts[1])
        signature = base64url_to_bytes(parts[2])
    except binascii.Error as e:
        raise AuthInvalidJwtError("Invalid JWT structure") from e

    return DecodedJWT(
        header=JWTHeader.model_validate_json(header),
        payload=JWTPayload.model_validate_json(payload),
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


def redirect_to_as_query(redirect_to: str | None) -> QueryParams:
    if redirect_to:
        return QueryParams({"redirect_to": redirect_to})
    return QueryParams()
