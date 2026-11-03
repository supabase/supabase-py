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
