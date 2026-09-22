from deprecation import fail_if_not_removed
from storage3.utils import SyncClient, merge_file_options


@fail_if_not_removed
def test_sync_client() -> None:
    client = SyncClient()
    # Verify that aclose method exists and calls close
    assert hasattr(client, "aclose")
    assert callable(client.aclose)
    client.aclose()  # Should not raise any exception


def test_merge_file_options_normalizes_only_content_type() -> None:
    options = merge_file_options(
        {
            "Content-Type": "application/pdf",
            "X-Custom-Header": "custom-value",
        }
    )

    assert options["content-type"] == "application/pdf"
    assert "Content-Type" not in options
    assert options["X-Custom-Header"] == "custom-value"
