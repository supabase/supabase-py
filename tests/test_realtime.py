import supabase


def test_realtime_client_initialization() -> None:
    ref = "ooqqmozurnggtljmjkii"
    url = f"https://{ref}.supabase.co"
    # Sample JWT Key
    key = "xxxxxxxxxxxxxx.xxxxxxxxxxxxxxx.xxxxxxxxxxxxxxx"
    sp = supabase.Client(url, key)
    assert sp.realtime_url == f"wss://{ref}.supabase.co/realtime/v1"

    url = "http://localhost:54322"
    sp_local = supabase.Client(url, key)
    assert sp_local.realtime_url == "ws://localhost:54322/realtime/v1"


def test_sync_realtime():
    ref = "ooqqmozurnggtljmjkii"
    url = f"https://{ref}.supabase.co"
    # Sample JWT Key
    key = "xxxxxxxxxxxxxx.xxxxxxxxxxxxxxx.xxxxxxxxxxxxxxx"
    sp = supabase.Client(url, key)

    try:
        sp.realtime.channel("test")
    except NotImplementedError:
        pass
