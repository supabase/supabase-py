from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, NamedTuple, TypeGuard

from pydantic import BaseModel

from .helpers import generate_pkce_challenge
from .types import AuthChangeEvent

if TYPE_CHECKING:
    from supabase_utils.types import JSON

_PASSWORD_RECOVERY_MARKER = "PASSWORD_RECOVERY"
_MAX_PENDING_PKCE_FLOWS = 5
_FLOW_ID_PARAMETER = "sb_flow_id"
_FLOW_ID_PATTERN = re.compile(r"[A-Za-z0-9_-]{8,64}")


class _PKCEFlow(NamedTuple):
    flow_id: str
    code_verifier: str


def _is_valid_flow_id(flow_id: object) -> TypeGuard[str]:
    return isinstance(flow_id, str) and _FLOW_ID_PATTERN.fullmatch(flow_id) is not None


def _parse_flow_index(raw: str | None) -> list[str]:
    """The storage may be client controlled, like a cookie, so anything that
    is not a flow id is dropped before it is used in a storage key."""
    if raw is None:
        return []
    try:
        index: object = json.loads(raw)
    except ValueError:
        return []
    if not isinstance(index, list):
        return []
    flow_ids: list[object] = index
    return [flow_id for flow_id in flow_ids if _is_valid_flow_id(flow_id)]


def _append_flow_id(redirect_to: str, flow_id: str) -> str:
    """Edits the URL as a string, so custom schemes and the encoding of the
    other parameters stay as they are."""
    url, hash_sign, fragment = redirect_to.partition("#")
    path, _, query = url.partition("?")
    parameters = [
        parameter
        for parameter in query.split("&")
        if parameter and parameter.partition("=")[0] != _FLOW_ID_PARAMETER
    ]
    parameters.append(f"{_FLOW_ID_PARAMETER}={flow_id}")
    return f"{path}?{'&'.join(parameters)}{hash_sign}{fragment}"


def _push_flow(index: list[str], flow_id: str) -> tuple[list[str], list[str]]:
    index = [pending for pending in index if pending != flow_id] + [flow_id]
    cut = max(len(index) - _MAX_PENDING_PKCE_FLOWS, 0)
    return index[cut:], index[:cut]


def _pkce_challenge_params(code_verifier: str) -> dict[str, str]:
    code_challenge = generate_pkce_challenge(code_verifier)
    code_challenge_method = "plain" if code_verifier == code_challenge else "s256"
    return {
        "code_challenge": code_challenge,
        "code_challenge_method": code_challenge_method,
    }


def _with_pkce_challenge(
    body: BaseModel | dict[str, JSON], pkce_flow: _PKCEFlow | None
) -> BaseModel | dict[str, JSON]:
    if pkce_flow is None:
        return body
    if isinstance(body, BaseModel):
        body = body.model_dump(mode="json", exclude_none=True)
    return {**body, **_pkce_challenge_params(pkce_flow.code_verifier)}


def _parse_code_verifier(code_verifier: str) -> tuple[str, AuthChangeEvent]:
    """
    Splits a stored code verifier into the verifier to send and the event the
    exchange notifies, which is `PASSWORD_RECOVERY` when the verifier carries
    the password recovery suffix.
    """
    verifier, _, suffix = code_verifier.partition("/")
    if suffix == _PASSWORD_RECOVERY_MARKER:
        return verifier, AuthChangeEvent.PASSWORD_RECOVERY
    return verifier, AuthChangeEvent.SIGNED_IN


def _stored_code_verifier(code_verifier: str, password_recovery: bool) -> str:
    if password_recovery:
        return f"{code_verifier}/{_PASSWORD_RECOVERY_MARKER}"
    return code_verifier
