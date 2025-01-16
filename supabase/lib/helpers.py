import re
from typing import Dict

BASE64URL_REGEX = r"^([a-z0-9_-]{4})*($|[a-z0-9_-]{3}$|[a-z0-9_-]{2}$)$"


def is_valid_jwt(value: str) -> bool:
    """Checks if value looks like a JWT, does not do any extra parsing."""
    if not isinstance(value, str):
        return False

    # Remove trailing whitespaces if any.
    value = value.strip()

    # Remove "Bearer " prefix if any.
    if value.startswith("Bearer "):
        value = value[7:]

    # Valid JWT must have 2 dots (Header.Paylod.Signature)
    if value.count(".") != 2:
        return False

    for part in value.split("."):
        if not re.search(BASE64URL_REGEX, part, re.IGNORECASE):
            return False

    return True


def check_authorization_header(headers: Dict[str, str]):
    authorization = headers.get("Authorization")
    if not authorization:
        return

    if authorization.startswith("Bearer "):
        if not is_valid_jwt(authorization):
            raise ValueError(
                "create_client called with global Authorization header that does not contain a JWT"
            )

    return True
