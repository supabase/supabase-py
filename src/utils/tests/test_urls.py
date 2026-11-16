import pytest

from supabase_utils._urls import is_loopback_host


@pytest.mark.parametrize(
    "host", ["localhost", "127.0.0.1", "127.12.0.1", "127.255.255.255", "::1"]
)
def test_is_loopback_host(host: str) -> None:
    assert is_loopback_host(host)


@pytest.mark.parametrize(
    "host",
    [
        None,
        "",
        "LOCALHOST",
        "localhost.",
        "api.localhost",
        "localhost.example.com",
        "0.0.0.0",
        "10.0.2.2",
        "128.0.0.1",
        "0127.0.0.1",
        "127.000.0.1",
        "127.1",
        "0x7f.0.0.1",
        "::2",
        "::ffff:127.0.0.1",
        "::1%eth0",
    ],
)
def test_is_not_loopback_host(host: str | None) -> None:
    assert not is_loopback_host(host)
