from __future__ import annotations

import base64
import hashlib
import re
import secrets
import string
import uuid
from base64 import urlsafe_b64decode
from datetime import datetime
from json import loads
from typing import Any, Dict, Optional, Type, TypedDict, TypeVar, cast
from urllib.parse import urlparse

from httpx import HTTPStatusError, Response
from pydantic import BaseModel

from .constants import API_VERSION_HEADER_NAME, API_VERSIONS, BASE64URL_REGEX
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


def model_validate(model: Type[TBaseModel], contents) -> TBaseModel:
    """Compatibility layer between pydantic 1 and 2 for parsing an instance
    of a BaseModel from varied"""
    try:
        # pydantic > 2
        return model.model_validate(contents)
    except AttributeError:
        # pydantic < 2
        return model.parse_obj(contents)


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


def parse_auth_response(data: Any) -> AuthResponse:
    session: Optional[Session] = None
    if (
        "access_token" in data
        and "refresh_token" in data
        and "expires_in" in data
        and data["access_token"]
        and data["refresh_token"]
        and data["expires_in"]
    ):
        session = model_validate(Session, data)
    user_data = data.get("user", data)
    user = model_validate(User, user_data) if user_data else None
    return AuthResponse(session=session, user=user)


def parse_auth_otp_response(data: Any) -> AuthOtpResponse:
    return model_validate(AuthOtpResponse, data)


def parse_link_identity_response(data: Any) -> LinkIdentityResponse:
    return model_validate(LinkIdentityResponse, data)


def parse_link_response(data: Any) -> GenerateLinkResponse:
    properties = GenerateLinkProperties(
        action_link=data.get("action_link"),
        email_otp=data.get("email_otp"),
        hashed_token=data.get("hashed_token"),
        redirect_to=data.get("redirect_to"),
        verification_type=data.get("verification_type"),
    )
    user = model_validate(
        User, {k: v for k, v in data.items() if k not in model_dump(properties)}
    )
    return GenerateLinkResponse(properties=properties, user=user)


def parse_user_response(data: Any) -> UserResponse:
    if "user" not in data:
        data = {"user": data}
    return model_validate(UserResponse, data)


def parse_sso_response(data: Any) -> SSOResponse:
    return model_validate(SSOResponse, data)


def parse_jwks(response: Any) -> JWKSet:
    if "keys" not in response or len(response["keys"]) == 0:
        raise AuthInvalidJwtError("JWKS is empty")

    return {"keys": response["keys"]}


def get_error_message(error: Any) -> str:
    props = ["msg", "message", "error_description", "error"]
    filter = lambda prop: (
        prop in error if isinstance(error, dict) else hasattr(error, prop)
    )
    return next((error[prop] for prop in props if filter(prop)), str(error))


def get_error_code(error: Any) -> str:
    return error.get("error_code", None) if isinstance(error, dict) else None


def looks_like_http_status_error(exception: Exception) -> bool:
    return isinstance(exception, HTTPStatusError)


def handle_exception(exception: Exception) -> AuthError:
    if not looks_like_http_status_error(exception):
        return AuthRetryableError(get_error_message(exception), 0)
    error = cast(HTTPStatusError, exception)
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
            and datetime.timestamp(response_api_version)
            >= API_VERSIONS.get("2024-01-01").get("timestamp")
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
                and len(data.get("weak_password"))
            ):
                return AuthWeakPasswordError(
                    get_error_message(data),
                    error.response.status_code,
                    data.get("weak_password").get("reasons"),
                )
        elif error_code == "weak_password":
            return AuthWeakPasswordError(
                get_error_message(data),
                error.response.status_code,
                data.get("weak_password", {}).get("reasons", {}),
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


def decode_jwt(token: str) -> DecodedJWT:
    parts = token.split(".")
    if len(parts) != 3:
        raise AuthInvalidJwtError("Invalid JWT structure")

    # regex check for base64url
    for part in parts:
        if not re.match(BASE64URL_REGEX, part, re.IGNORECASE):
            raise AuthInvalidJwtError("JWT not in base64url format")

    return DecodedJWT(
        header=JWTHeader(**loads(str_from_base64url(parts[0]))),
        payload=JWTPayload(**loads(str_from_base64url(parts[1]))),
        signature=base64url_to_bytes(parts[2]),
        raw={
            "header": parts[0],
            "payload": parts[1],
        },
    )


def generate_pkce_verifier(length=64):
    """Generate a random PKCE verifier of the specified length."""
    if length < 43 or length > 128:
        raise ValueError("PKCE verifier length must be between 43 and 128 characters")

    # Define characters that can be used in the PKCE verifier
    charset = string.ascii_letters + string.digits + "-._~"

    return "".join(secrets.choice(charset) for _ in range(length))


def generate_pkce_challenge(code_verifier):
    """Generate a code challenge from a PKCE verifier."""
    # Hash the verifier using SHA-256
    verifier_bytes = code_verifier.encode("utf-8")
    sha256_hash = hashlib.sha256(verifier_bytes).digest()

    return base64.urlsafe_b64encode(sha256_hash).rstrip(b"=").decode("utf-8")


API_VERSION_REGEX = r"^2[0-9]{3}-(0[1-9]|1[0-2])-(0[1-9]|1[0-9]|2[0-9]|3[0-1])$"


def parse_response_api_version(response: Response):
    api_version = response.headers.get(API_VERSION_HEADER_NAME)

    if not api_version:
        return None

    if re.search(API_VERSION_REGEX, api_version) is None:
        return None

    try:
        dt = datetime.strptime(api_version, "%Y-%m-%d")
        return dt
    except Exception as e:
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
