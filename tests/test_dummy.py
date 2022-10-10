import supabase


def test_client_initialization() -> None:
    sp = supabase.Client("http://testwebsite.com", "atestapi")
    func = sp.functions()
