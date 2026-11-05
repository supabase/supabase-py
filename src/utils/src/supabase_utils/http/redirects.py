from yarl import URL

CREDENTIAL_HEADERS = ("apikey", "authorization")


def keeps_credentials(source: URL, target: URL) -> bool:
    if source.host != target.host:
        return False
    if source.scheme == target.scheme:
        return source.port == target.port
    return (source.scheme, source.port, target.scheme, target.port) == (
        "http",
        80,
        "https",
        443,
    )
