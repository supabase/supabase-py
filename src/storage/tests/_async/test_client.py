from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from dataclasses import dataclass
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient as HttpxClient
from httpx import HTTPStatusError, Response
from supabase_utils.http import AsyncExecutor

from storage3 import AsyncStorageClient, StorageFileApiClient
from storage3.exceptions import StorageApiError, StorageException
from storage3.types import TransformOptions

from ..utils import AsyncFinalizerFactory

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Callable


# Global variable to track the ids from the buckets created in the tests run
temp_test_buckets_ids: list[str] = []


@pytest.fixture
def uuid_factory() -> Callable[[], str]:
    def method() -> str:
        """Generate a 8 digits long UUID"""
        return uuid4().hex[:8]

    return method


@pytest.fixture
def delete_left_buckets(
    request: pytest.FixtureRequest,
    storage: AsyncStorageClient,
) -> None:
    """Ensures no test buckets are left when a test that created a bucket fails"""

    async def afinalizer() -> None:
        for bucket_id in temp_test_buckets_ids:
            try:
                await storage.empty_bucket(bucket_id)
                await storage.delete_bucket(bucket_id)
            except StorageException as e:
                # Ignore 404 responses since they mean the bucket was already deleted
                response = e.args[0]
                if response["statusCode"] != 404:
                    raise e
                continue

    request.addfinalizer(AsyncFinalizerFactory(afinalizer).finalizer)


@pytest.fixture
async def bucket(
    storage: AsyncStorageClient, uuid_factory: Callable[[], str]
) -> AsyncGenerator[str]:
    """Creates a test bucket which will be used in the whole storage tests run and deleted at the end"""
    bucket_id = uuid_factory()

    # Store bucket_id in global list
    global temp_test_buckets_ids
    temp_test_buckets_ids.append(bucket_id)

    await storage.create_bucket(id=bucket_id)

    yield bucket_id

    await storage.empty_bucket(bucket_id)
    await storage.delete_bucket(bucket_id)

    temp_test_buckets_ids.remove(bucket_id)


@pytest.fixture
async def public_bucket(
    storage: AsyncStorageClient, uuid_factory: Callable[[], str]
) -> AsyncGenerator[str]:
    """Creates a test public bucket which will be used in the whole storage tests run and deleted at the end"""
    bucket_id = uuid_factory()

    # Store bucket_id in global list
    global temp_test_buckets_ids
    temp_test_buckets_ids.append(bucket_id)

    await storage.create_bucket(id=bucket_id, public=True)

    yield bucket_id

    await storage.empty_bucket(bucket_id)
    await storage.delete_bucket(bucket_id)

    temp_test_buckets_ids.remove(bucket_id)


@pytest.fixture
def storage_file_client(
    storage: AsyncStorageClient, bucket: str
) -> Generator[StorageFileApiClient[AsyncExecutor]]:
    """Creates the storage file client for the whole storage tests run"""
    yield storage.from_(bucket)


@pytest.fixture
def storage_file_client_public(
    storage: AsyncStorageClient, public_bucket: str
) -> Generator[StorageFileApiClient[AsyncExecutor]]:
    """Creates the storage file client for the whole storage tests run"""
    yield storage.from_(public_bucket)


@dataclass
class FileForTesting:
    name: str
    local_path: str
    bucket_folder: str
    bucket_path: str
    mime_type: str
    file_content: bytes


@pytest.fixture
def file(tmp_path: Path, uuid_factory: Callable[[], str]) -> FileForTesting:
    """Creates a different test file (same content but different path) for each test"""
    file_name = "test_image.svg"
    file_content = (
        b'<svg width="109" height="113" viewBox="0 0 109 113" fill="none" xmlns="http://www.w3.org/2000/svg"> '
        b'<path d="M63.7076 110.284C60.8481 113.885 55.0502 111.912 54.9813 107.314L53.9738 40.0627L99.1935 '
        b'40.0627C107.384 40.0627 111.952 49.5228 106.859 55.9374L63.7076 110.284Z" fill="url(#paint0_linear)"/> '
        b'<path d="M63.7076 110.284C60.8481 113.885 55.0502 111.912 54.9813 107.314L53.9738 40.0627L99.1935 '
        b'40.0627C107.384 40.0627 111.952 49.5228 106.859 55.9374L63.7076 110.284Z" fill="url(#paint1_linear)" '
        b'fill-opacity="0.2"/> <path d="M45.317 2.07103C48.1765 -1.53037 53.9745 0.442937 54.0434 5.041L54.4849 '
        b'72.2922H9.83113C1.64038 72.2922 -2.92775 62.8321 2.1655 56.4175L45.317 2.07103Z" fill="#3ECF8E"/> <defs>'
        b'<linearGradient id="paint0_linear" x1="53.9738" y1="54.974" x2="94.1635" y2="71.8295"'
        b'gradientUnits="userSpaceOnUse"> <stop stop-color="#249361"/> <stop offset="1" stop-color="#3ECF8E"/> '
        b'</linearGradient> <linearGradient id="paint1_linear" x1="36.1558" y1="30.578" x2="54.4844" y2="65.0806" '
        b'gradientUnits="userSpaceOnUse"> <stop/> <stop offset="1" stop-opacity="0"/> </linearGradient> </defs> </svg>'
    )
    bucket_folder = uuid_factory()
    bucket_path = f"{bucket_folder}/{file_name}"
    file_path = tmp_path / file_name
    with open(file_path, "wb") as f:
        f.write(file_content)

    return FileForTesting(
        name=file_name,
        local_path=str(file_path),
        bucket_folder=bucket_folder,
        bucket_path=bucket_path,
        mime_type="image/svg+xml",
        file_content=file_content,
    )


@pytest.fixture
def two_files(tmp_path: Path, uuid_factory: Callable[[], str]) -> list[FileForTesting]:
    """Creates multiple test files (different content, same bucket/folder path, different file names)"""
    file_name_1 = "test_image_1.svg"
    file_name_2 = "test_image_2.svg"
    file_content = (
        b'<svg width="109" height="113" viewBox="0 0 109 113" fill="none" xmlns="http://www.w3.org/2000/svg"> '
        b'<path d="M63.7076 110.284C60.8481 113.885 55.0502 111.912 54.9813 107.314L53.9738 40.0627L99.1935 '
        b'40.0627C107.384 40.0627 111.952 49.5228 106.859 55.9374L63.7076 110.284Z" fill="url(#paint0_linear)"/> '
        b'<path d="M63.7076 110.284C60.8481 113.885 55.0502 111.912 54.9813 107.314L53.9738 40.0627L99.1935 '
        b'40.0627C107.384 40.0627 111.952 49.5228 106.859 55.9374L63.7076 110.284Z" fill="url(#paint1_linear)" '
        b'fill-opacity="0.2"/> <path d="M45.317 2.07103C48.1765 -1.53037 53.9745 0.442937 54.0434 5.041L54.4849 '
        b'72.2922H9.83113C1.64038 72.2922 -2.92775 62.8321 2.1655 56.4175L45.317 2.07103Z" fill="#3ECF8E"/> <defs>'
        b'<linearGradient id="paint0_linear" x1="53.9738" y1="54.974" x2="94.1635" y2="71.8295"'
        b'gradientUnits="userSpaceOnUse"> <stop stop-color="#249361"/> <stop offset="1" stop-color="#3ECF8E"/> '
        b'</linearGradient> <linearGradient id="paint1_linear" x1="36.1558" y1="30.578" x2="54.4844" y2="65.0806" '
        b'gradientUnits="userSpaceOnUse"> <stop/> <stop offset="1" stop-opacity="0"/> </linearGradient> </defs> </svg>'
    )
    file_content_2 = (
        b'<svg width="119" height="123" viewBox="0 0 119 123" fill="none" xmlns="http://www.w3.org/2000/svg"> '
        b'<path d="M63.7076 110.284C60.8481 113.885 55.0502 111.912 54.9813 107.314L53.9738 40.0627L99.1935 '
        b'40.0627C107.384 40.0627 111.952 49.5228 106.859 55.9374L63.7076 110.284Z" fill="url(#paint0_linear)"/> '
        b'<path d="M63.7076 110.284C60.8481 113.885 55.0502 111.912 54.9813 107.314L53.9738 40.0627L99.1935 '
        b'40.0627C107.384 40.0627 111.952 49.5228 106.859 55.9374L63.7076 110.284Z" fill="url(#paint1_linear)" '
        b'fill-opacity="0.2"/> <path d="M45.317 2.07103C48.1765 -1.53037 53.9745 0.442937 54.0434 5.041L54.4849 '
        b'72.2922H9.83113C1.64038 72.2922 -2.92775 62.8321 2.1655 56.4175L45.317 2.07103Z" fill="#3FDF8E"/> <defs>'
        b'<linearGradient id="paint0_linear" x1="53.9738" y1="54.974" x2="94.1635" y2="71.8295"'
        b'gradientUnits="userSpaceOnUse"> <stop stop-color="#249361"/> <stop offset="1" stop-color="#3FDF8E"/> '
        b'</linearGradient> <linearGradient id="paint1_linear" x1="36.1558" y1="30.578" x2="54.4844" y2="65.0806" '
        b'gradientUnits="userSpaceOnUse"> <stop/> <stop offset="1" stop-opacity="0"/> </linearGradient> </defs> </svg>'
    )
    bucket_folder = uuid_factory()
    bucket_path_1 = f"{bucket_folder}/{file_name_1}"
    bucket_path_2 = f"{bucket_folder}/{file_name_2}"
    file_path_1 = tmp_path / file_name_1
    file_path_2 = tmp_path / file_name_2
    with open(file_path_1, "wb") as f:
        f.write(file_content)
    with open(file_path_2, "wb") as f:
        f.write(file_content_2)

    return [
        FileForTesting(
            name=file_name_1,
            local_path=str(file_path_1),
            bucket_folder=bucket_folder,
            bucket_path=bucket_path_1,
            mime_type="image/svg+xml",
            file_content=file_content,
        ),
        FileForTesting(
            name=file_name_2,
            local_path=str(file_path_2),
            bucket_folder=bucket_folder,
            bucket_path=bucket_path_2,
            mime_type="image/svg+xml",
            file_content=file_content_2,
        ),
    ]


@pytest.fixture
def multi_file(tmp_path: Path, uuid_factory: Callable[[], str]) -> list[FileForTesting]:
    """Creates multiple test files (same content, same bucket/folder path, different file names)"""
    file_name_1 = "test_image_1.svg"
    file_name_2 = "test_image_2.svg"
    file_content = (
        b'<svg width="109" height="113" viewBox="0 0 109 113" fill="none" xmlns="http://www.w3.org/2000/svg"> '
        b'<path d="M63.7076 110.284C60.8481 113.885 55.0502 111.912 54.9813 107.314L53.9738 40.0627L99.1935 '
        b'40.0627C107.384 40.0627 111.952 49.5228 106.859 55.9374L63.7076 110.284Z" fill="url(#paint0_linear)"/> '
        b'<path d="M63.7076 110.284C60.8481 113.885 55.0502 111.912 54.9813 107.314L53.9738 40.0627L99.1935 '
        b'40.0627C107.384 40.0627 111.952 49.5228 106.859 55.9374L63.7076 110.284Z" fill="url(#paint1_linear)" '
        b'fill-opacity="0.2"/> <path d="M45.317 2.07103C48.1765 -1.53037 53.9745 0.442937 54.0434 5.041L54.4849 '
        b'72.2922H9.83113C1.64038 72.2922 -2.92775 62.8321 2.1655 56.4175L45.317 2.07103Z" fill="#3ECF8E"/> <defs>'
        b'<linearGradient id="paint0_linear" x1="53.9738" y1="54.974" x2="94.1635" y2="71.8295"'
        b'gradientUnits="userSpaceOnUse"> <stop stop-color="#249361"/> <stop offset="1" stop-color="#3ECF8E"/> '
        b'</linearGradient> <linearGradient id="paint1_linear" x1="36.1558" y1="30.578" x2="54.4844" y2="65.0806" '
        b'gradientUnits="userSpaceOnUse"> <stop/> <stop offset="1" stop-opacity="0"/> </linearGradient> </defs> </svg>'
    )
    bucket_folder = uuid_factory()
    bucket_path_1 = f"{bucket_folder}/{file_name_1}"
    bucket_path_2 = f"{bucket_folder}/{file_name_2}"
    file_path_1 = tmp_path / file_name_1
    file_path_2 = tmp_path / file_name_2
    with open(file_path_1, "wb") as f:
        f.write(file_content)
    with open(file_path_2, "wb") as f:
        f.write(file_content)

    return [
        FileForTesting(
            name=file_name_1,
            local_path=str(file_path_1),
            bucket_folder=bucket_folder,
            bucket_path=bucket_path_1,
            mime_type="image/svg+xml",
            file_content=file_content,
        ),
        FileForTesting(
            name=file_name_2,
            local_path=str(file_path_2),
            bucket_folder=bucket_folder,
            bucket_path=bucket_path_2,
            mime_type="image/svg+xml",
            file_content=file_content,
        ),
    ]


async def test_client_upload(
    storage_file_client: StorageFileApiClient[AsyncExecutor], file: FileForTesting
) -> None:
    """Ensure we can upload files to a bucket"""
    await storage_file_client.upload(
        path=file.bucket_path, file=file.local_path, content_type=file.mime_type
    )

    image = await storage_file_client.download(file.bucket_path)
    files = await storage_file_client.list(file.bucket_folder)
    image_info = next((f for f in files if f.name == file.name), None)

    assert image == file.file_content
    assert image_info is not None
    assert image_info.metadata.get("mimetype") == file.mime_type


async def test_client_upload_with_query(
    storage_file_client: StorageFileApiClient[AsyncExecutor], file: FileForTesting
) -> None:
    """Ensure we can upload files to a bucket, even with query parameters"""
    await storage_file_client.upload(
        file.bucket_path, file.local_path, content_type=file.mime_type
    )

    image = await storage_file_client.download(
        file.bucket_path, query_params={"my-param": "test"}
    )
    files = await storage_file_client.list(file.bucket_folder)
    image_info = next((f for f in files if f.name == file.name), None)

    assert image == file.file_content
    assert image_info is not None
    assert image_info.metadata.get("mimetype") == file.mime_type


async def test_client_download_with_query_doesnt_lose_params(
    storage_file_client: StorageFileApiClient[AsyncExecutor], file: FileForTesting
) -> None:
    """Ensure query params aren't lost"""
    from yarl import URL

    params = {"my-param": "test"}
    mock_response = Mock()
    with patch.object(HttpxClient, "send") as mock_request:
        mock_request.return_value = mock_response
        await storage_file_client.download(file.bucket_path, query_params=params)
        expected_url = storage_file_client.base_url.joinpath(
            "object", storage_file_client.id, *URL(file.bucket_path).parts
        ).with_query(params)

        (actual_request,) = mock_request.call_args[0]
        actual_url = str(actual_request.url)

        assert URL(actual_url).query == params
        assert str(expected_url) == actual_url


async def test_client_update(
    storage_file_client: StorageFileApiClient[AsyncExecutor],
    two_files: list[FileForTesting],
) -> None:
    """Ensure we can upload files to a bucket"""
    await storage_file_client.upload(
        two_files[0].bucket_path,
        two_files[0].local_path,
        content_type=two_files[0].mime_type,
    )

    await storage_file_client.update(
        two_files[0].bucket_path,
        two_files[1].local_path,
        content_type=two_files[1].mime_type,
    )

    image = await storage_file_client.download(two_files[0].bucket_path)
    file_list = await storage_file_client.list(two_files[0].bucket_folder)
    image_info = next((f for f in file_list if f.name == two_files[0].name), None)

    assert image == two_files[1].file_content
    assert image_info is not None
    assert image_info.metadata.get("mimetype") == two_files[1].mime_type


@pytest.mark.parametrize(
    "path", ["foobar.txt", "example/nested.jpg", "/leading/slash.png"]
)
async def test_client_create_signed_upload_url(
    storage_file_client: StorageFileApiClient[AsyncExecutor], path: str
) -> None:
    """Ensure we can create signed URLs to upload files to a bucket"""
    data = await storage_file_client.create_signed_upload_url(path)
    expected_url = storage_file_client.base_url.joinpath(
        "object", "upload", "sign", storage_file_client.id, *path.lstrip("/").split("/")
    )
    assert data.signed_url.startswith(str(expected_url))


async def test_client_upload_to_signed_url(
    storage_file_client: StorageFileApiClient[AsyncExecutor], file: FileForTesting
) -> None:
    """Ensure we can upload to a signed URL with various options"""
    # Test with content-type
    data = await storage_file_client.create_signed_upload_url(file.bucket_path)

    await storage_file_client.upload_to_signed_url(
        file.bucket_path, data.token, file.file_content, content_type=file.mime_type
    )
    image = await storage_file_client.download(file.bucket_path)
    files = await storage_file_client.list(file.bucket_folder)
    image_info = next((f for f in files if f.name == file.name), None)

    assert image == file.file_content
    assert image_info is not None
    assert image_info.metadata.get("mimetype") == file.mime_type

    # Test with file_options=None
    data = await storage_file_client.create_signed_upload_url(
        f"no_options_{file.bucket_path}"
    )
    await storage_file_client.upload_to_signed_url(
        f"no_options_{file.bucket_path}", data.token, file.file_content
    )
    image = await storage_file_client.download(f"no_options_{file.bucket_path}")
    assert image == file.file_content

    # Test with cache-control
    data = await storage_file_client.create_signed_upload_url(
        f"cached_{file.bucket_path}"
    )
    await storage_file_client.upload_to_signed_url(
        f"cached_{file.bucket_path}",
        data.token,
        file.file_content,
        cache_control="3600",
    )
    cached_info = await storage_file_client.info(f"cached_{file.bucket_path}")
    assert cached_info.cache_control == "max-age=3600"


async def test_client_create_signed_url(
    storage_file_client: StorageFileApiClient[AsyncExecutor], file: FileForTesting
) -> None:
    """Ensure we can create and use signed URLs with various options"""
    await storage_file_client.upload(
        file.bucket_path, file.local_path, content_type=file.mime_type
    )

    # Test basic signed URL
    signed_url = await storage_file_client.create_signed_url(file.bucket_path, 60)
    async with HttpxClient(timeout=None) as client:
        response = await client.get(signed_url)
    response.raise_for_status()
    assert response.content == file.file_content

    # Test with download option
    download_signed_url = await storage_file_client.create_signed_url(
        file.bucket_path, 60, download="custom_download.svg"
    )
    async with HttpxClient(timeout=None) as client:
        response = await client.get(download_signed_url)

    response.raise_for_status()
    assert (
        response.headers["content-disposition"]
        == "attachment; filename=custom_download.svg; filename*=UTF-8''custom_download.svg"
    )
    assert response.content == file.file_content

    # Test with transform options
    transform_signed_url = await storage_file_client.create_signed_url(
        file.bucket_path,
        60,
        transform=TransformOptions(width=200, height=200, resize="cover"),
    )
    # assert "width=200" in transform_signed_url["signedURL"]
    # assert "height=200" in transform_signed_url["signedURL"]
    # assert "resize=cover" in transform_signed_url["signedURL"]
    # assert "format=png" in transform_signed_url["signedURL"]
    async with HttpxClient(timeout=None) as client:
        response = await client.get(transform_signed_url)
    response.raise_for_status()


async def test_client_create_signed_urls(
    storage_file_client: StorageFileApiClient[AsyncExecutor],
    multi_file: list[FileForTesting],
) -> None:
    """Ensure we can create signed urls for files in a bucket"""
    paths = []
    for file in multi_file:
        paths.append(file.bucket_path)
        await storage_file_client.upload(
            file.bucket_path, file.local_path, content_type=file.mime_type
        )

    signed_urls = await storage_file_client.create_signed_urls(paths, 10)

    async with HttpxClient() as client:
        for url in signed_urls:
            response = await client.get(url.signed_url)
            response.raise_for_status()
            assert response.content == multi_file[0].file_content


async def test_client_get_public_url(
    storage_file_client_public: StorageFileApiClient[AsyncExecutor],
    file: FileForTesting,
) -> None:
    """Ensure we can get the public url of a file in a bucket with various options"""
    await storage_file_client_public.upload(
        file.bucket_path, file.local_path, content_type=file.mime_type
    )

    # Test basic public URL
    public_url = storage_file_client_public.get_public_url(file.bucket_path)
    async with HttpxClient(timeout=None) as client:
        response = await client.get(public_url)
    response.raise_for_status()
    assert response.content == file.file_content

    # Test with download option
    download_url = storage_file_client_public.get_public_url(
        file.bucket_path, download="custom_name.svg"
    )
    async with HttpxClient(timeout=None) as client:
        response = await client.get(download_url)
    response.raise_for_status()
    assert (
        response.headers["content-disposition"]
        == "attachment; filename=custom_name.svg; filename*=UTF-8''custom_name.svg"
    )
    assert response.content == file.file_content

    # Test with transform options
    transform_url = storage_file_client_public.get_public_url(
        file.bucket_path,
        transform=TransformOptions(width=100, height=100, resize="contain"),
    )
    assert "width=100" in transform_url
    assert "height=100" in transform_url
    assert "resize=contain" in transform_url


async def test_client_upload_with_custom_metadata(
    storage_file_client_public: StorageFileApiClient[AsyncExecutor],
    file: FileForTesting,
) -> None:
    """Ensure we can get the public url of a file in a bucket"""
    await storage_file_client_public.upload(
        file.bucket_path,
        file.local_path,
        content_type=file.mime_type,
        metadata={"custom": "metadata", "second": "second", "third": "third"},
    )

    info = await storage_file_client_public.info(file.bucket_path)
    assert info.name == file.bucket_path
    assert info.metadata == {
        "custom": "metadata",
        "second": "second",
        "third": "third",
    }


async def test_client_info(
    storage_file_client_public: StorageFileApiClient[AsyncExecutor],
    file: FileForTesting,
) -> None:
    """Ensure we can get the public url of a file in a bucket"""
    await storage_file_client_public.upload(
        file.bucket_path, file.local_path, content_type=file.mime_type
    )

    info = await storage_file_client_public.info(file.bucket_path)
    assert info.name == file.bucket_path
    assert info.content_type == file.mime_type


async def test_client_info_with_error(
    storage_file_client_public: StorageFileApiClient[AsyncExecutor],
    file: FileForTesting,
) -> None:
    """Ensure we can get the public url of a file in a bucket"""
    await storage_file_client_public.upload(
        file.bucket_path, file.local_path, content_type=file.mime_type
    )

    """Ensure StorageException is raised when signed URL creation fails"""
    mock_error_response = Mock(spec=Response)
    mock_error_response.status_code = 404
    mock_error_response.content = b'{"error": "Custom error message", "statusCode": 404, "message": "File not found"}'

    mock_response = Mock(spec=Response)
    mock_response.json.return_value = {"error": "Custom error message"}
    mock_response.raise_for_status.side_effect = HTTPStatusError(
        "HTTP Error", request=Mock(), response=mock_error_response
    )

    with patch.object(
        storage_file_client_public.executor.session, "send", new_callable=AsyncMock
    ) as mock_request:
        mock_request.return_value = mock_response

        with pytest.raises(StorageApiError):
            await storage_file_client_public.info(file.bucket_path)


async def test_client_exists(
    storage_file_client_public: StorageFileApiClient[AsyncExecutor],
    file: FileForTesting,
) -> None:
    """Ensure we can get the public url of a file in a bucket"""
    await storage_file_client_public.upload(
        file.bucket_path, file.local_path, content_type=file.mime_type
    )

    exists = await storage_file_client_public.exists(file.bucket_path)

    assert exists


async def test_client_copy(
    storage_file_client: StorageFileApiClient[AsyncExecutor], file: FileForTesting
) -> None:
    """Ensure we can copy files within a bucket"""
    # Upload original file
    await storage_file_client.upload(
        file.bucket_path, file.local_path, content_type=file.mime_type
    )

    # Copy to new path
    new_path = f"{file.bucket_folder}/copied_{file.name}"
    await storage_file_client.copy(file.bucket_path, new_path)

    # Verify both files exist and have same content
    original = await storage_file_client.download(file.bucket_path)
    copied = await storage_file_client.download(new_path)
    assert original == copied == file.file_content

    # Verify metadata was copied
    files = await storage_file_client.list(file.bucket_folder)
    copied_info = next((f for f in files if f.name == f"copied_{file.name}"), None)
    assert copied_info is not None
    assert copied_info.metadata.get("mimetype") == file.mime_type


async def test_client_move(
    storage_file_client: StorageFileApiClient[AsyncExecutor], file: FileForTesting
) -> None:
    """Ensure we can move files within a bucket"""
    # Upload original file
    await storage_file_client.upload(
        file.bucket_path, file.local_path, content_type=file.mime_type
    )

    # Move to new path
    new_path = f"{file.bucket_folder}/moved_{file.name}"
    await storage_file_client.move(file.bucket_path, new_path)

    # Verify original doesn't exist
    assert not await storage_file_client.exists(file.bucket_path)

    # Verify moved file exists with correct content
    moved = await storage_file_client.download(new_path)
    assert moved == file.file_content

    # Verify metadata was preserved
    files = await storage_file_client.list(file.bucket_folder)
    moved_info = next((f for f in files if f.name == f"moved_{file.name}"), None)
    assert moved_info is not None
    assert moved_info.metadata.get("mimetype") == file.mime_type


async def test_client_remove(
    storage_file_client: StorageFileApiClient[AsyncExecutor], file: FileForTesting
) -> None:
    """Ensure we can remove files from a bucket"""
    # Upload file
    await storage_file_client.upload(
        file.bucket_path, file.local_path, content_type=file.mime_type
    )

    # Verify file exists
    assert await storage_file_client.exists(file.bucket_path)

    # Remove file
    await storage_file_client.remove([file.bucket_path])

    # Verify file no longer exists
    assert not await storage_file_client.exists(file.bucket_path)


async def test_client_remove_multiple(
    storage_file_client: StorageFileApiClient[AsyncExecutor],
    multi_file: list[FileForTesting],
) -> None:
    """Ensure we can remove multiple files from a bucket"""
    # Upload files
    paths = []
    for file in multi_file:
        await storage_file_client.upload(
            file.bucket_path, file.local_path, content_type=file.mime_type
        )
        paths.append(file.bucket_path)

    # Verify files exist
    for path in paths:
        assert await storage_file_client.exists(path)

    # Remove files
    await storage_file_client.remove(paths)

    # Verify files no longer exist
    for path in paths:
        assert not await storage_file_client.exists(path)


async def test_client_create_signed_urls_with_download(
    storage_file_client: StorageFileApiClient[AsyncExecutor],
    multi_file: list[FileForTesting],
) -> None:
    """Ensure we can create signed urls with download options for files in a bucket"""
    paths = []
    for file in multi_file:
        paths.append(file.bucket_path)
        await storage_file_client.upload(
            file.bucket_path, file.local_path, content_type=file.mime_type
        )

    signed_urls = await storage_file_client.create_signed_urls(paths, 10, download=True)

    async with HttpxClient() as client:
        for i, url in enumerate(signed_urls):
            response = await client.get(url.signed_url)
            response.raise_for_status()
            assert response.content == multi_file[i].file_content


async def test_client_list_v2(
    storage_file_client: StorageFileApiClient[AsyncExecutor], file: FileForTesting
) -> None:
    """Ensure we can upload files to a bucket"""
    await storage_file_client.upload(
        file.bucket_path, file.local_path, content_type=file.mime_type
    )

    result = await storage_file_client.list_v2()

    assert not result.hasNext
    assert len(result.folders) == 0
    assert len(result.objects) == 1
    object = result.objects[0]
    assert object.name == file.bucket_path
    assert object.metadata.get("mimetype") == file.mime_type


async def test_client_list_v2_folder(
    storage_file_client: StorageFileApiClient[AsyncExecutor], file: FileForTesting
) -> None:
    """Ensure we can upload files to a bucket"""
    await storage_file_client.upload(
        file.bucket_path, file.local_path, content_type=file.mime_type
    )

    result = await storage_file_client.list_v2(with_delimiter=True)

    assert not result.hasNext
    assert len(result.objects) == 0
    assert len(result.folders) == 1
    folder = result.folders[0]
    assert folder.key == file.bucket_folder


async def test_client_list_v2_paginated(
    storage_file_client: StorageFileApiClient[AsyncExecutor], file: FileForTesting
) -> None:
    """Ensure we can upload files to a bucket"""
    suffixes = ["zz", "bb", "xx", "ww", "cc", "aa", "yy", "oo"]
    for suffix in suffixes:
        await storage_file_client.upload(
            file.bucket_path + suffix, file.local_path, content_type=file.mime_type
        )

    has_next = True
    cursor = ""
    pages = 0
    while has_next:
        result = await storage_file_client.list_v2(
            with_delimiter=True,
            prefix=f"{file.bucket_folder}/",
            limit=2,
            cursor=cursor,
        )
        has_next = result.hasNext
        cursor = result.nextCursor or ""

        assert len(result.objects) == 2
        assert all(f.name.startswith(file.bucket_path) for f in result.objects)
        pages += 1
    assert pages == 4
