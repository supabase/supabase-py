import pytest
from supabase_utils.http.redirects import keeps_credentials
from yarl import URL


@pytest.mark.parametrize(
    "target",
    [
        "https://project.supabase.co/other",
        "https://project.supabase.co:443/other",
        "https://PROJECT.supabase.co/other",
    ],
)
def test_keeps_credentials_on_same_origin(target: str) -> None:
    assert keeps_credentials(URL("https://project.supabase.co/x"), URL(target))


def test_keeps_credentials_on_https_upgrade() -> None:
    assert keeps_credentials(
        URL("http://project.supabase.co/x"), URL("https://project.supabase.co/x")
    )


@pytest.mark.parametrize(
    ("source", "target"),
    [
        ("https://project.supabase.co/x", "https://attacker.example/x"),
        ("https://project.supabase.co/x", "https://sub.project.supabase.co/x"),
        ("https://project.supabase.co/x", "http://project.supabase.co/x"),
        ("https://project.supabase.co/x", "https://project.supabase.co:8443/x"),
        ("http://project.supabase.co:8080/x", "https://project.supabase.co/x"),
        ("http://project.supabase.co/x", "https://project.supabase.co:8443/x"),
    ],
)
def test_drops_credentials_on_cross_origin(source: str, target: str) -> None:
    assert not keeps_credentials(URL(source), URL(target))
