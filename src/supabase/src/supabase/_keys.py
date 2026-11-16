from __future__ import annotations

import base64
import binascii
import json
import platform
from typing import TYPE_CHECKING

from .errors import SupabaseException
from .version import __version__

if TYPE_CHECKING:
    from collections.abc import Mapping

_DEFAULT_HEADERS = {
    "X-Client-Info": (
        f"supabase-py/{__version__}"
        f"; platform={platform.system()}"
        f"; platform-version={platform.release()}"
        f"; runtime=python"
        f"; runtime-version={platform.python_version()}"
    )
}


def _validate_string_argument(name: str, value: object) -> None:
    if value is not None and not isinstance(value, str):
        raise SupabaseException(f"{name} must be a string, not {type(value).__name__}")
    if not value:
        raise SupabaseException(f"{name} is required")


def _find_authorization(headers: Mapping[str, str]) -> str | None:
    return next(
        (value for key, value in headers.items() if key.lower() == "authorization"),
        None,
    )


def _is_new_api_key(key: str) -> bool:
    return key.startswith("sb_")


def _is_secret_key(key: str) -> bool:
    if key.startswith("sb_secret_"):
        return True
    parts = key.split(".")
    if len(parts) != 3:
        return False
    try:
        payload = json.loads(
            base64.urlsafe_b64decode(parts[1] + "=" * (-len(parts[1]) % 4))
        )
    except (binascii.Error, ValueError):
        return False
    return isinstance(payload, dict) and payload.get("role") == "service_role"
