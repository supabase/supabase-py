from __future__ import annotations

import base64
import binascii
import hashlib
import re
import secrets
import string
import uuid
from base64 import urlsafe_b64decode
from datetime import datetime
from typing import Any, Dict, Optional, Type, TypedDict, TypeVar, Union
from urllib.parse import urlparse

from httpx import HTTPStatusError, Response
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


def model_validate(model: Type[TBaseModel], contents: Union[str, bytes]) -> TBaseModel:
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
        session = model_validate(Session, response.content)
        user = session.user
    except ValidationError:
        session = None
        user = model_validate(User, response.content)
    return AuthResponse(user=user, session=session)


def parse_auth_otp_response(response: Response) -> AuthOtpResponse:
    return model_validate(AuthOtpResponse, response.content)


def parse_link_identity_response(response: Response) -> LinkIdentityResponse:
    return model_validate(LinkIdentityResponse, response.content)


def parse_link_response(response: Response) -> GenerateLinkResponse:
    properties = model_validate(GenerateLinkProperties, response.content)
    user = model_validate(User, response.content)
    return GenerateLinkResponse(properties=properties, user=user)


UserParser: TypeAdapter = TypeAdapter(Union[UserResponse, User])


def parse_user_response(response: Response) -> UserResponse:
    parsed = UserParser.validate_json(response.content)
    return UserResponse(user=parsed) if isinstance(parsed, User) else parsed


def parse_sso_response(response: Response) -> SSOResponse:
    return model_validate(SSOResponse, response.content)


JWKSetParser = TypeAdapter(JWKSet)


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


def handle_exception(error: HTTPStatusError | RuntimeError) -> AuthError:
    if not isinstance(error, HTTPStatusError):
        return AuthRetryableError(get_error_message(error), 0)
    try:
        network_error_codes = [502, 503, 504]
        if error.response.status_code in network_error_codes:
            return AuthRetryableError(
                get_error_message(error), error.response.status_code
            )
        data = error.response.json()

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
            if (
                isinstance(data, dict)
                and data
                and isinstance(data.get("weak_password"), dict)
                and data.get("weak_password")
                and isinstance(data.get("weak_password"), list)
                and len(data["weak_password"])
            ):
                return AuthWeakPasswordError(
                    get_error_message(data),
                    error.response.status_code,
                    data["weak_password"].get("reasons"),
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


class DecodedJWT(TypedDict):
    header: JWTHeader
    payload: JWTPayload
    signature: bytes
    raw: Dict[str, str]


JWTHeaderParser = TypeAdapter(JWTHeader)
JWTPayloadParser = TypeAdapter(JWTPayload)


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
        header=JWTHeaderParser.validate_json(header),
        payload=JWTPayloadParser.validate_json(payload),
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


def parse_response_api_version(response: Response) -> Optional[datetime]:
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


def validate_exp(exp: int) -> None:
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
