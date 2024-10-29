import re


BASE64URL_REGEX = r"^([a-z0-9_-]{4})*($|[a-z0-9_-]{3}$|[a-z0-9_-]{2}$)$"


def is_jwt(value: str) -> bool:
    if value.startswith("Bearer "):
        value = value.replace("Bearer ", "")

    value = value.strip()
    if not value:
        return False

    parts = value.split(".")
    if len(parts) != 3:
        return False

    # loop through the parts and test against regex
    for part in parts:
        if len(part) < 4 or not re.search(BASE64URL_REGEX, part, re.IGNORECASE):
            return False

    return True


def check_authorization_header(headers):
    return True
