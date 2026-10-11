from email import policy
from email.parser import BytesParser
from typing import Literal, cast

import pytest
from httpx import AsyncClient, Client, MockTransport, Request, Response
from storage3 import AsyncStorageClient, SyncStorageClient
from storage3.types import FileOptions, UploadSignedUrlFileOptions

UploadMethod = Literal["upload", "update", "upload_to_signed_url"]
FILE_CONTENTS = b"%PDF-1.4\nexample document\n"


def assert_multipart_upload(request: Request) -> Response:
    content_type = request.headers["content-type"]
    assert content_type.startswith("multipart/form-data; boundary=")

    message = BytesParser(policy=policy.default).parsebytes(
        f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode()
        + request.content
    )
    parts = {
        part.get_param("name", header="content-disposition"): part
        for part in message.iter_parts()
    }
    assert parts["file"].get_content_type() == "application/pdf"
    assert parts["file"].get_payload(decode=True) == FILE_CONTENTS
    assert parts["cacheControl"].get_payload(decode=True) == b"7200"
    assert parts["metadata"].get_payload(decode=True) == b'{"DocumentType": "PDF"}'
    assert request.headers["x-custom-header"] == "custom-value"

    if request.method == "POST":
        assert request.headers["x-upsert"] == "false"
    elif "/upload/sign/" not in request.url.path:
        assert "x-upsert" not in request.headers

    return Response(200, json={"Key": "documents/report.pdf"})


@pytest.mark.parametrize("method", ["upload", "update", "upload_to_signed_url"])
@pytest.mark.parametrize(
    "header_name", ["content-type", "Content-Type", "CONTENT-TYPE"]
)
def test_sync_upload_preserves_multipart_content_type(
    method: UploadMethod, header_name: str
) -> None:
    file_options = {
        header_name: "application/pdf",
        "cache-control": "7200",
        "metadata": {"DocumentType": "PDF"},
        "headers": {"x-custom-header": "custom-value"},
    }
    with Client(transport=MockTransport(assert_multipart_upload)) as http:
        storage = SyncStorageClient(
            "https://example.com/storage/v1/", {}, http_client=http
        )
        bucket = storage.from_("documents")
        if method == "upload_to_signed_url":
            response = bucket.upload_to_signed_url(
                "report.pdf",
                "test-upload-token",
                FILE_CONTENTS,
                cast(UploadSignedUrlFileOptions, file_options),
            )
        elif method == "update":
            response = bucket.update(
                "report.pdf", FILE_CONTENTS, cast(FileOptions, file_options)
            )
        else:
            response = bucket.upload(
                "report.pdf", FILE_CONTENTS, cast(FileOptions, file_options)
            )

    assert response.path == "report.pdf"
    assert response.full_path == "documents/report.pdf"
    assert file_options[header_name] == "application/pdf"


@pytest.mark.parametrize("method", ["upload", "update", "upload_to_signed_url"])
@pytest.mark.parametrize(
    "header_name", ["content-type", "Content-Type", "CONTENT-TYPE"]
)
async def test_async_upload_preserves_multipart_content_type(
    method: UploadMethod, header_name: str
) -> None:
    file_options = {
        header_name: "application/pdf",
        "cache-control": "7200",
        "metadata": {"DocumentType": "PDF"},
        "headers": {"x-custom-header": "custom-value"},
    }
    async with AsyncClient(transport=MockTransport(assert_multipart_upload)) as http:
        storage = AsyncStorageClient(
            "https://example.com/storage/v1/", {}, http_client=http
        )
        bucket = storage.from_("documents")
        if method == "upload_to_signed_url":
            response = await bucket.upload_to_signed_url(
                "report.pdf",
                "test-upload-token",
                FILE_CONTENTS,
                cast(UploadSignedUrlFileOptions, file_options),
            )
        elif method == "update":
            response = await bucket.update(
                "report.pdf", FILE_CONTENTS, cast(FileOptions, file_options)
            )
        else:
            response = await bucket.upload(
                "report.pdf", FILE_CONTENTS, cast(FileOptions, file_options)
            )

    assert response.path == "report.pdf"
    assert response.full_path == "documents/report.pdf"
    assert file_options[header_name] == "application/pdf"
