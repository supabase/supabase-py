import importlib
from types import ModuleType

import postgrest
import pytest
import realtime
import storage3
import supabase_auth
import supabase_functions
from supabase_utils.errors import SupabaseError
from supabase_utils.http.errors import (
    RequestTimeoutError,
    SupabaseAPIError,
    SupabaseTransportError,
)

import supabase
import supabase.client
import supabase.httpx

PACKAGES = [
    "postgrest",
    "realtime",
    "storage3",
    "supabase",
    "supabase.client",
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
                "UserDoesNotExistError",
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
        (
            realtime,
            [
                "AuthorizationError",
                "ChannelJoinError",
                "NotConnectedError",
                "RealtimeError",
                "RealtimeTimeoutError",
            ],
        ),
    ],
)
def test_errors_are_exported_from_package_and_supabase(
    package: ModuleType, names: list[str]
) -> None:
    for name in names:
        assert name in package.__all__
        assert name in supabase.__all__
        assert getattr(supabase, name) is getattr(package, name)


@pytest.mark.parametrize("name", ["create_async_client", "create_client"])
def test_httpx_factories_are_exported_from_supabase(name: str) -> None:
    assert name in supabase.__all__
    assert getattr(supabase, name) is getattr(supabase.httpx, name)


def test_postgrest_error_is_exported_from_supabase() -> None:
    assert supabase.PostgrestAPIError is postgrest.APIError


@pytest.mark.parametrize(
    ("name", "error"),
    [
        ("RequestTimeoutError", RequestTimeoutError),
        ("SupabaseAPIError", SupabaseAPIError),
        ("SupabaseError", SupabaseError),
        ("SupabaseTransportError", SupabaseTransportError),
    ],
)
def test_shared_errors_are_exported_from_supabase(
    name: str, error: type[SupabaseError]
) -> None:
    assert name in supabase.__all__
    assert getattr(supabase, name) is error


def test_every_exported_error_is_a_supabase_error() -> None:
    for name in supabase.__all__:
        symbol = getattr(supabase, name)
        if isinstance(symbol, type) and issubclass(symbol, BaseException):
            assert issubclass(symbol, SupabaseError), name


@pytest.mark.parametrize(
    "name",
    [
        "AsyncTableExecutor",
        "Column",
        "ComputedField",
        "Filter",
        "FunctionCall",
        "NullableColumn",
        "PartialRow",
        "Table",
        "TableExecutor",
        "TableRequest",
        "TableResult",
        "ToManyRelation",
        "ToOneRelation",
    ],
)
def test_typed_api_is_exported_from_supabase(name: str) -> None:
    assert name in supabase.__all__
    assert getattr(supabase, name) is getattr(postgrest, name)
