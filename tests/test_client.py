from __future__ import annotations

from typing import Any

import pytest


@pytest.mark.xfail(
    reason="None of these values should be able to instanciate a client object"
)
@pytest.mark.parametrize("url", ["", None, "valeefgpoqwjgpj", 139, -1, {}, []])
@pytest.mark.parametrize("key", ["", None, "valeefgpoqwjgpj", 139, -1, {}, []])
def test_incorrect_values_dont_instanciate_client(url: Any, key: Any) -> None:
    """Ensure we can't instanciate client with nonsense values."""
    from supabase import Client, create_client

    _: Client = create_client(url, key)
