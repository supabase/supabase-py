import httpx
import pytest
from storage3 import SyncStorageClient
from storage3.exceptions import StorageApiError


def error_handler(status_code: int) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code,
            json={
                "statusCode": status_code,
                "error": "InternalError" if status_code == 500 else "NotFound",
                "message": "Internal server error"
                if status_code == 500
                else "Resource not found",
            },
            request=request,
        )

    return httpx.MockTransport(handler)


def test_get_vector_bucket_propagates_server_errors() -> None:
    with httpx.Client(transport=error_handler(500)) as http:
        client = SyncStorageClient(
            "https://example.supabase.co/storage/v1/",
            {},
            http_client=http,
        )

        with pytest.raises(StorageApiError, match="Internal server error"):
            client.vectors().get_bucket("embeddings")


def test_get_vector_index_propagates_server_errors() -> None:
    with httpx.Client(transport=error_handler(500)) as http:
        client = SyncStorageClient(
            "https://example.supabase.co/storage/v1/",
            {},
            http_client=http,
        )

        with pytest.raises(StorageApiError, match="Internal server error"):
            client.vectors().from_("embeddings").get_index("documents")


def test_get_vector_resources_return_none_when_not_found() -> None:
    with httpx.Client(transport=error_handler(404)) as http:
        client = SyncStorageClient(
            "https://example.supabase.co/storage/v1/",
            {},
            http_client=http,
        )

        assert client.vectors().get_bucket("missing") is None
        assert client.vectors().from_("missing").get_index("missing") is None
