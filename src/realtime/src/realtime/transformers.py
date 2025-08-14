import re


def http_endpoint_url(socket_url: str) -> str:
    url = re.sub(r"^ws", "http", socket_url, flags=re.IGNORECASE)
    url = re.sub(
        r"(\/socket\/websocket|\/socket|\/websocket)\/?$", "", url, flags=re.IGNORECASE
    )
    return re.sub(r"\/+$", "", url)
