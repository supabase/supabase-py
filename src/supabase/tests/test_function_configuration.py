import supabase


def test_functions_client_initialization() -> None:
    ref = "ooqqmozurnggtljmjkii"
    url = f"https://{ref}.supabase.co"
    # Sample JWT Key
    key = "xxxxxxxxxxxxxx.xxxxxxxxxxxxxxx.xxxxxxxxxxxxxxx"
    sp = supabase.Client(url, key)
    assert sp.functions_url == f"https://{ref}.supabase.co/functions/v1"

    url = "https://localhost:54322"
    sp_local = supabase.Client(url, key)
    assert sp_local.functions_url == f"{url}/functions/v1"
