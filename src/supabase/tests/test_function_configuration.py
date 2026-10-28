import supabase


def test_functions_client_initialization() -> None:
    ref = "ooqqmozurnggtljmjkii"
    url = f"https://{ref}.supabase.co"
    # Sample JWT Key
    key = "xxxxxxxxxxxxxx.xxxxxxxxxxxxxxx.xxxxxxxxxxxxxxx"
    sp = supabase.Client(url, key)
    assert str(sp.functions_url) == f"https://{ref}.supabase.co/functions/v1"

    url = "https://localhost:54322"
    sp_local = supabase.Client(url, key)
    assert str(sp_local.functions_url) == f"{url}/functions/v1"
    
def test_supabase_client_service_urls() -> None:
    ref = "ooqqmozurnggtljmjkii"
    url = f"https://{ref}.supabase.co"
    key = "xxxxxxxxxxxxxx.xxxxxxxxxxxxxxx.xxxxxxxxxxxxxxx"
    sp = supabase.Client(url, key)

    assert str(sp.rest_url) == f"{url}/rest/v1"
    assert str(sp.auth_url) == f"{url}/auth/v1"
    assert str(sp.storage_url) == f"{url}/storage/v1/"