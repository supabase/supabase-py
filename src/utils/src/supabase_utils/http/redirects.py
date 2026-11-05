from yarl import URL

CREDENTIAL_HEADERS = ("apikey", "authorization")


def is_same_origin(source: URL, target: URL) -> bool:
    return (source.scheme, source.host, source.port) == (
        target.scheme,
        target.host,
        target.port,
    )
