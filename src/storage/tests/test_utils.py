from deprecation import fail_if_not_removed

from storage3.utils import SyncClient


@fail_if_not_removed
def test_sync_client():
    client = SyncClient()
    # Verify that aclose method exists and calls close
    assert hasattr(client, "aclose")
    assert callable(client.aclose)
    client.aclose()  # Should not raise any exception
