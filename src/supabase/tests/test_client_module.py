import supabase
import supabase.client


def test_client_module_reexports_package_api() -> None:
    for name in supabase.__all__:
        assert getattr(supabase.client, name) is getattr(supabase, name)


def test_client_module_keeps_legacy_aliases() -> None:
    from supabase._async.auth_client import AsyncSupabaseAuthClient
    from supabase._async.client import AsyncStorageClient

    assert supabase.client.AsyncSupabaseAuthClient is AsyncSupabaseAuthClient
    assert supabase.client.AsyncSupabaseStorageClient is AsyncStorageClient


def test_client_module_star_import_matches_all() -> None:
    namespace: dict[str, object] = {}
    exec("from supabase.client import *", namespace)
    exported = {name for name in namespace if name != "__builtins__"}
    assert exported == set(supabase.client.__all__)
    assert set(supabase.__all__) <= exported
