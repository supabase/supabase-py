from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import ValidationError
from supabase_auth.types import AuthMFAEnrollResponse, Session

USER: dict[str, Any] = {
    "id": "user-id",
    "app_metadata": {},
    "user_metadata": {},
    "aud": "authenticated",
    "created_at": "2024-01-01T00:00:00Z",
}


def session_data(**overrides: Any) -> dict[str, Any]:
    return {
        "access_token": "access",
        "refresh_token": "refresh",
        "expires_in": 3600,
        "token_type": "bearer",
        "user": USER,
        **overrides,
    }


def test_session_computes_expires_at_without_mutating_input() -> None:
    data = session_data()

    session = Session.model_validate(data)

    assert session.expires_at is not None
    assert "expires_at" not in data


def test_session_keeps_given_expires_at() -> None:
    session = Session.model_validate(session_data(expires_at=123))

    assert session.expires_at == 123


@pytest.mark.parametrize("value", [None, "not a session", 1])
def test_session_rejects_non_dict_input_with_validation_error(value: Any) -> None:
    with pytest.raises(ValidationError):
        Session.model_validate(value)


def test_mfa_enroll_response_requires_phone_for_phone_type() -> None:
    with pytest.raises(ValidationError):
        AuthMFAEnrollResponse.model_validate(
            {"id": "factor-id", "type": "phone", "friendly_name": "phone"}
        )


@pytest.mark.parametrize("value", [None, "not a response", 1])
def test_mfa_enroll_response_rejects_non_dict_input_with_validation_error(
    value: Any,
) -> None:
    with pytest.raises(ValidationError):
        AuthMFAEnrollResponse.model_validate(value)


def test_mfa_enroll_response_requires_phone_for_phone_type_from_attributes() -> None:
    with pytest.raises(ValidationError):
        AuthMFAEnrollResponse.model_validate(
            SimpleNamespace(
                id="factor-id",
                type="phone",
                friendly_name="phone",
                totp=None,
                phone=None,
            ),
            from_attributes=True,
        )
