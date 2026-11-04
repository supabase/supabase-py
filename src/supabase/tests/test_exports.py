import importlib
from types import ModuleType

import postgrest
import pytest
import realtime
import storage3
import supabase_auth
import supabase_functions

import supabase

PACKAGES = [
    "postgrest",
    "realtime",
    "storage3",
    "supabase",
    "supabase_auth",
    "supabase_functions",
    "supabase_utils",
]


@pytest.mark.parametrize("name", PACKAGES)
def test_package_declares_all(name: str) -> None:
    module = importlib.import_module(name)
    exported = module.__dict__.get("__all__")
    assert exported is not None
    assert len(set(exported)) == len(exported)
    for symbol in exported:
        assert hasattr(module, symbol), f"{name}.{symbol}"


@pytest.mark.parametrize(
    ("package", "names"),
    [
        (
            supabase_auth,
            [
                "AuthApiError",
                "AuthError",
                "AuthImplicitGrantRedirectError",
                "AuthInvalidCredentialsError",
                "AuthInvalidJwtError",
                "AuthRetryableError",
                "AuthSessionMissingError",
                "AuthUnknownError",
                "AuthWeakPasswordError",
                "CustomAuthError",
                "UserDoesntExist",
            ],
        ),
        (
            storage3,
            ["StorageApiError", "StorageException", "VectorBucketException"],
        ),
        (
            supabase_functions,
            ["FunctionsError", "FunctionsHttpError", "FunctionsRelayError"],
        ),
        (realtime, ["AuthorizationError", "NotConnectedError"]),
    ],
)
def test_errors_are_exported_from_package_and_supabase(
    package: ModuleType, names: list[str]
) -> None:
    for name in names:
        assert name in package.__all__
        assert name in supabase.__all__
        assert getattr(supabase, name) is getattr(package, name)


def test_postgrest_error_is_exported_from_supabase() -> None:
    assert supabase.PostgrestAPIError is postgrest.APIError
