from __future__ import annotations

import ipaddress
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Collection

    from yarl import URL

_IPV4_LOOPBACK = ipaddress.IPv4Network("127.0.0.0/8")
_IPV6_LOOPBACK = ipaddress.IPv6Address("::1")


def is_loopback_host(host: str | None) -> bool:
    if not host:
        return False
    if host == "localhost":
        return True
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return False
    if isinstance(address, ipaddress.IPv4Address):
        # Browsers and inet_aton read a part with a leading zero as octal, so
        # 0127.0.0.1 is 87.0.0.1 to them. Only the canonical form is trusted.
        return address in _IPV4_LOOPBACK and str(address) == host
    return address == _IPV6_LOOPBACK


def check_secure_url(
    url: URL,
    *,
    name: str,
    secure_schemes: Collection[str],
    insecure_schemes: Collection[str],
    allow_insecure_http: bool,
    example: str,
) -> None:
    """
    Raise a `ValueError` unless `url` is absolute and uses one of
    `secure_schemes`, or one of `insecure_schemes` with a loopback host or
    `allow_insecure_http` set.

    The message shows `url` without its credentials, query and fragment.
    """
    shown = repr(_redact(url))
    if not url.is_absolute() or not url.host:
        raise ValueError(
            f"{name} {shown} must be an absolute URL with a host, such as {example}"
        )
    if url.scheme in secure_schemes:
        return
    if url.scheme in insecure_schemes:
        if allow_insecure_http or is_loopback_host(url.host):
            return
        raise ValueError(
            f"{name} {shown} must use {_either(secure_schemes)}, since "
            f"{url.scheme} sends the API key and the session of the user in "
            f"clear text. {url.scheme} is only accepted for a loopback host, "
            "such as localhost, or when allow_insecure_http is set"
        )
    raise ValueError(
        f"{name} {shown} must use {_either([*secure_schemes, *insecure_schemes])}"
    )


def _either(schemes: Collection[str]) -> str:
    *rest, last = schemes
    return f"{', '.join(rest)} or {last}" if rest else last


def _redact(url: URL) -> str:
    url = url.with_query(None).with_fragment(None)
    if url.is_absolute() and url.host:
        url = url.with_user(None)
    return str(url)
