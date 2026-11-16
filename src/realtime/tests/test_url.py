import pytest
from yarl import URL

from realtime import RealtimeClient
from realtime.client import connect_once


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("ws://localhost:54321/realtime/v1", "http://localhost:54321"),
        ("wss://project.supabase.co/realtime/v1", "https://project.supabase.co"),
        ("http://localhost:54321/realtime/v1", "http://localhost:54321"),
        ("https://project.supabase.co/realtime/v1", "https://project.supabase.co"),
        ("ws://10.0.2.2:54321/realtime/v1", "http://10.0.2.2:54321"),
    ],
)
def test_http_endpoint_maps_the_websocket_scheme(url: str, expected: str) -> None:
    client = RealtimeClient(url, allow_insecure_http=True)

    assert client.http_endpoint == URL(expected)


@pytest.mark.parametrize(
    "url",
    [
        "ws://localhost:54321/realtime/v1",
        "http://LOCALHOST:54321/realtime/v1",
        "ws://127.0.0.1:54321/realtime/v1",
        "http://127.12.0.1/realtime/v1",
        "ws://[::1]:54321/realtime/v1",
        "http://[0:0:0:0:0:0:0:1]/realtime/v1",
    ],
)
def test_accepts_an_insecure_url_on_a_loopback_host(url: str) -> None:
    client = RealtimeClient(url)

    assert client.url == URL(url)


@pytest.mark.parametrize(
    "url",
    [
        "ws://project.supabase.co/realtime/v1",
        "http://192.168.1.20:8000/realtime/v1",
        "ws://10.0.2.2:54321/realtime/v1",
        "ws://0.0.0.0:54321/realtime/v1",
        "ws://realtime.localhost/realtime/v1",
        "ws://localhost.example.com/realtime/v1",
        "ws://127.0.0.1.example.com/realtime/v1",
        "ws://0127.0.0.1/realtime/v1",
        "ws://127.000.0.1/realtime/v1",
        "ws://127.1/realtime/v1",
        "ws://[::2]/realtime/v1",
        "ws://[::ffff:7f00:1]/realtime/v1",
    ],
)
def test_rejects_an_insecure_url_on_another_host(url: str) -> None:
    with pytest.raises(ValueError, match="must use wss or https, since"):
        RealtimeClient(url)


@pytest.mark.parametrize(
    "url", ["ftp://localhost/realtime/v1", "ftp://project.supabase.co"]
)
def test_rejects_another_scheme(url: str) -> None:
    with pytest.raises(ValueError, match="must use"):
        RealtimeClient(url, allow_insecure_http=True)


@pytest.mark.parametrize("url", ["", "localhost/realtime/v1", "wss://", "wss:///a"])
def test_rejects_a_url_without_a_host(url: str) -> None:
    with pytest.raises(ValueError, match="must be an absolute URL with a host"):
        RealtimeClient(url)


@pytest.mark.parametrize(
    "url",
    [
        "wss://project.supabase.co/realtime/v1",
        "https://project.supabase.co/realtime/v1",
    ],
)
def test_accepts_a_secure_url_on_any_host(url: str) -> None:
    client = RealtimeClient(url)

    assert client.url == URL(url)


def test_allow_insecure_http_accepts_any_host() -> None:
    client = RealtimeClient(
        "ws://192.168.1.20:8000/realtime/v1", allow_insecure_http=True
    )

    assert client.http_endpoint == URL("http://192.168.1.20:8000")


def test_connect_once_passes_allow_insecure_http_on() -> None:
    with pytest.raises(ValueError, match="allow_insecure_http"):
        connect_once("ws://192.168.1.20:8000/realtime/v1")

    connection = connect_once(
        "ws://192.168.1.20:8000/realtime/v1", allow_insecure_http=True
    )

    assert connection.client.url == URL("ws://192.168.1.20:8000/realtime/v1")
