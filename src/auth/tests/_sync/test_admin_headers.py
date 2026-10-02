from supabase_auth import SyncGoTrueAdminAPI, SyncGoTrueClient


def test_admin_api_does_not_share_the_client_header_dict() -> None:
    """The admin API must hold its own headers.

    `GoTrueClient` passes its own `_headers` to the admin API. If that dict is
    shared, anything that later rewrites the client's `Authorization` header
    also rewrites the admin one, and admin calls silently run with the user's
    token instead of the service key.
    """
    client = SyncGoTrueClient(
        url="http://localhost:9998",
        headers={"Authorization": "Bearer service-key"},
        auto_refresh_token=False,
        persist_session=False,
    )

    assert client.admin._headers is not client._headers

    client._headers["Authorization"] = "Bearer user-token"

    assert client.admin._headers["Authorization"] == "Bearer service-key"


def test_caller_headers_are_copied() -> None:
    """A caller that keeps mutating the dict it passed in must not reach us."""
    caller_headers = {"Authorization": "Bearer service-key"}

    admin = SyncGoTrueAdminAPI(
        url="http://localhost:9998",
        headers=caller_headers,
        http_client=None,
    )

    caller_headers["Authorization"] = "Bearer user-token"

    assert admin._headers["Authorization"] == "Bearer service-key"
