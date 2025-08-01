from urllib.parse import urlparse


def is_ws_url(url: str) -> bool:
    return urlparse(url).scheme in {"wss", "ws", "http", "https"}
