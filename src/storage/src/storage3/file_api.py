from __future__ import annotations

import base64
import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, BinaryIO, Literal, Protocol, cast, overload

from pydantic import BaseModel, TypeAdapter
from supabase_utils.http.body import FileContent
from supabase_utils.http.headers import Headers
from supabase_utils.http.io import (
    AsyncHttpIO,
    HttpMethod,
    SyncHttpIO,
    handle_http_io,
)
from supabase_utils.http.query import URLQuery
from supabase_utils.http.request import (
    BytesRequest,
    EmptyRequest,
    JSONRequest,
    Response,
)
from supabase_utils.types import JSON, JSONParser
from yarl import URL

from .download import (
    AsyncStorageDownload,
    StorageDownload,
    _async_download,
    _async_read,
    _byte_range,
    _sync_download,
    _sync_read,
)
from .exceptions import (
    StorageException,
    _validate_adapter,
    _validate_model,
    parse_api_error,
)
from .progress import _counted_upload
from .resumable import (
    DEFAULT_CHUNK_SIZE,
    AsyncResumableUpload,
    ResumableUpload,
    ResumableUploadSource,
)
from .types import (
    CreateSignedUrlBody,
    CreateSignedUrlResponse,
    CreateSignedUrlsBody,
    FileObject,
    ListBody,
    ListResult,
    MessageResponse,
    SignedUploadURL,
    SignedUploadUrlResponse,
    SignedUrlJsonResponse,
    SignedUrlsJsonResponse,
    SortBy,
    TransformOptions,
    UploadBody,
    UploadResponse,
    transform_to_dict,
)

if TYPE_CHECKING:
    import builtins
    from collections.abc import (
        AsyncIterator,
        Coroutine,
        Generator,
        Iterator,
        MutableMapping,
    )
    from contextlib import AbstractAsyncContextManager, AbstractContextManager

    from supabase_utils.http.body import RequestContent

    from .progress import ProgressCallback

__all__ = ["StorageFileApiClient"]


def relative_path_to_parts(path: str) -> tuple[str, ...]:
    parts = tuple(path.lstrip("/").split("/"))
    if parts == ("",):
        raise ValueError(f"Object keys must not be empty: {path!r}")
    if {".", ".."} & set(parts):
        raise ValueError(f"Object keys must not contain dot segments: {path!r}")
    if "" in parts[:-1]:
        raise ValueError(f"Object keys must not contain empty segments: {path!r}")
    return parts


def _normalize_object_key(path: str) -> str:
    return "/".join(relative_path_to_parts(path))


def _bool_header(value: bool) -> str:
    if not isinstance(value, bool):
        raise TypeError(f"upsert must be a bool, not {type(value).__name__}")
    return "true" if value else "false"


def _cache_control_header(value: str | None) -> str | None:
    if value is not None and value.isdecimal():
        return f"max-age={value}"
    return value


def _url_query(download: bool | str | None, cache_nonce: str | None) -> URLQuery:
    query = URLQuery.empty()
    if download:
        query = query.set("download", "" if download is True else download)
    if cache_nonce:
        query = query.override("cacheNonce", cache_nonce)
    return query


@contextmanager
def _upload_content(
    file: UploadBody, on_progress: ProgressCallback | None
) -> Generator[RequestContent]:
    """The request body that streams `file`, with a file at a path open while
    it is sent and every chunk reported to `on_progress` until it returned."""
    with _raw_upload_content(file) as content:
        if on_progress is None:
            yield content
            return
        counted, progress = _counted_upload(content, on_progress)
        try:
            yield counted
        finally:
            progress.end()


@contextmanager
def _raw_upload_content(file: UploadBody) -> Generator[RequestContent]:
    if isinstance(file, bytes):
        yield file
    elif isinstance(file, (str, os.PathLike)):
        with open(file, "rb") as opened:
            yield FileContent(opened)
    elif hasattr(file, "read"):
        yield FileContent(cast("BinaryIO", file))
    else:
        yield file


def _upload_headers(
    content_type: str,
    cache_control: str,
    metadata: dict[str, Any] | None,
    upsert: bool | None,
    headers: dict[str, str] | None,
) -> Headers:
    http_headers = (
        Headers.empty()
        .set("Content-Type", content_type)
        .set("Cache-Control", f"max-age={cache_control}")
    )
    if metadata is not None:
        encoded = base64.b64encode(JSONParser.dump_json(metadata)).decode("ascii")
        http_headers = http_headers.set("x-metadata", encoded)
    if upsert is not None:
        http_headers = http_headers.set("x-upsert", _bool_header(upsert))
    if headers:
        http_headers = http_headers.update(Headers.from_mapping(headers))
    return http_headers


@dataclass(frozen=True)
class _ListOptions:
    prefix: str | None
    limit: int | None
    with_delimiter: bool | None
    sort_by: SortBy | None


def _sync_pages(
    client: StorageFileApiClient[SyncHttpIO], options: _ListOptions
) -> Iterator[ListResult]:
    cursor = None
    while True:
        page = client.list(
            options.prefix,
            limit=options.limit,
            cursor=cursor,
            with_delimiter=options.with_delimiter,
            sort_by=options.sort_by,
        )
        yield page
        cursor = _next_cursor(page, cursor)
        if cursor is None:
            return


async def _async_pages(
    client: StorageFileApiClient[AsyncHttpIO], options: _ListOptions
) -> AsyncIterator[ListResult]:
    cursor = None
    while True:
        page = await client.list(
            options.prefix,
            limit=options.limit,
            cursor=cursor,
            with_delimiter=options.with_delimiter,
            sort_by=options.sort_by,
        )
        yield page
        cursor = _next_cursor(page, cursor)
        if cursor is None:
            return


def _next_cursor(page: ListResult, cursor: str | None) -> str | None:
    if not page.hasNext or page.nextCursor is None:
        return None
    if page.nextCursor == cursor:
        raise StorageException(f"The listing did not advance past cursor {cursor!r}")
    return page.nextCursor


FileObjectsAdapter = TypeAdapter(list[FileObject])


class _UploadJsonResponse(BaseModel, extra="ignore"):
    Key: str
    Id: str | None = None
    version: str | None = None


def _parse_upload_response(response: Response, path: str) -> UploadResponse:
    data = _validate_model(response, _UploadJsonResponse)
    return UploadResponse(
        id=data.Id, path=path, full_path=data.Key, version=data.version
    )


class _HeadersSource(Protocol):
    @property
    def default_headers(self) -> Headers: ...


@dataclass
class StorageFileApiClient[HttpIO: (SyncHttpIO, AsyncHttpIO)]:
    """Functions needed to access the file API."""

    id: str
    base_url: URL
    executor: HttpIO
    client: _HeadersSource
    """The storage client this bucket belongs to, whose headers every
    request sends."""

    @property
    def default_headers(self) -> Headers:
        """The headers of the storage client, read for every request, so that
        a token the client got since this bucket was opened is sent."""
        return self.client.default_headers

    def _parse_signed_url_response(self, response: Response) -> SignedUploadURL:
        if not response.is_success:
            raise parse_api_error(response)
        signed_url_upload = SignedUploadUrlResponse.model_validate_json(
            response.content
        )
        path_parts = URL(signed_url_upload.url.lstrip("/"))
        url = self.base_url.join(path_parts)

        return SignedUploadURL(
            signed_url=str(url),
            token=signed_url_upload.token,
        )

    @handle_http_io
    def create_signed_upload_url(
        self,
        path: str,
        upsert: bool | None = None,
    ) -> HttpMethod[SignedUploadURL]:
        """
        Creates a signed upload URL.

        Args:
            path: The file path, including the file name. For example `folder/image.png`.
            upsert: Whether a later upload with the returned token may overwrite an
                existing file. The server default applies when omitted.

        Returns:
            The signed URL, and the token that `upload_to_signed_url` takes.
        """
        headers = Headers.empty()
        if upsert is not None:
            headers = headers.set("x-upsert", _bool_header(upsert))

        path_parts: tuple[str, ...] = relative_path_to_parts(path)
        response = yield EmptyRequest(
            method="POST",
            path=["object", "upload", "sign", self.id, *path_parts],
            headers=headers,
        )

        return self._parse_signed_url_response(response)

    @handle_http_io
    def upload_to_signed_url(
        self,
        path: str,
        token: str,
        file: UploadBody,
        content_type: str = "text/plain;charset=UTF-8",
        cache_control: str = "3600",
        metadata: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        *,
        on_progress: ProgressCallback | None = None,
    ) -> HttpMethod[UploadResponse]:
        """
        Upload a file with a token generated from `create_signed_upload_url`

        Args:
            path: The file path, including the file name
            token: The token generated from `create_signed_upload_url`
            file: What to upload: the bytes, the path of a file, a binary file or an
                iterator over the bytes. A file or an iterator is streamed instead
                of read into memory first.
            content_type: The `Content-Type` the file is stored with.
            cache_control: The number of seconds the file is cached in the browser and
                the Supabase CDN, sent as `Cache-Control: max-age=<seconds>`.
            metadata: Custom metadata stored with the file, a JSON object.
            headers: Extra headers sent with the request.
            on_progress: Called with the bytes sent so far and the total, or None when the
                total is not known, as the body is sent. It restarts from 0 when
                the body is sent again.

        Returns:
            The uploaded object.
        """
        path_parts: tuple[str, ...] = relative_path_to_parts(path)
        http_headers = _upload_headers(
            content_type, cache_control, metadata, upsert=False, headers=headers
        )
        with _upload_content(file, on_progress) as content:
            response = yield BytesRequest(
                method="PUT",
                path=["object", "upload", "sign", self.id, *path_parts],
                body=content,
                headers=http_headers,
                query=URLQuery.from_mapping({"token": token}),
            )

        return _parse_upload_response(response, "/".join(path_parts))

    def _make_signed_url(self, signed_url: str, url_query: URLQuery) -> str:
        url = URL(signed_url[1:])  # ignore starting slash
        signed = self.base_url.join(url).extend_query(url_query.as_query())
        return str(signed)

    def _parse_signed_url(self, response: Response, url_query: URLQuery) -> str:
        if not response.is_success:
            raise parse_api_error(response)
        signed_url_obj = SignedUrlJsonResponse.model_validate_json(response.content)
        return self._make_signed_url(signed_url_obj.signedURL, url_query)

    @handle_http_io
    def create_signed_url(
        self,
        path: str,
        expires_in: int,
        download: str | bool | None = None,
        transform: TransformOptions | None = None,
        *,
        cache_nonce: str | None = None,
    ) -> HttpMethod[str]:
        """
        Creates a signed URL, to share a file for a fixed amount of time.

        Args:
            path: file path to be downloaded, including the current file name.
            expires_in: number of seconds until the signed URL expires.
            download: `True` makes the URL download the file instead of showing it, and a
                file name does so under that name.
            transform: How to transform an image before it is served.
            cache_nonce: Appended to the URL as the `cacheNonce` query parameter. Pass a new
                value, such as the time the file last changed, to bypass a cached copy.

        Returns:
            The signed URL.
        """
        url_query = _url_query(download, cache_nonce)

        path_parts: tuple[str, ...] = relative_path_to_parts(path)
        body = CreateSignedUrlBody(
            expiresIn=expires_in,
            download=download,
            transform=transform,
        )
        response = yield JSONRequest(
            method="POST",
            path=["object", "sign", self.id, *path_parts],
            body=body,
            exclude_none=True,
        )

        return self._parse_signed_url(response, url_query)

    def _parse_signed_urls(
        self, response: Response, url_query: URLQuery
    ) -> builtins.list[CreateSignedUrlResponse]:
        if not response.is_success:
            raise parse_api_error(response)
        data = SignedUrlsJsonResponse.validate_json(response.content)
        signed_urls = []
        for item in data:
            # Prepare URL
            url = (
                self._make_signed_url(item.signedURL, url_query)
                if item.signedURL
                else None
            )
            signed_item = CreateSignedUrlResponse(
                error=item.error,
                path=item.path,
                signed_url=url,
            )
            signed_urls.append(signed_item)
        return signed_urls

    @handle_http_io
    def create_signed_urls(
        self,
        paths: builtins.list[str],
        expires_in: int,
        download: bool | str | None = None,
        *,
        cache_nonce: str | None = None,
    ) -> HttpMethod[builtins.list[CreateSignedUrlResponse]]:
        """
        Creates signed URLs for several files, to share them for a fixed amount
        of time.

        Args:
            paths: the file paths to be downloaded, each including the current file name.
            expires_in: number of seconds until the signed URL expires.
            download: `True` makes the URL download the file instead of showing it, and a
                file name does so under that name.
            cache_nonce: Appended to the URL as the `cacheNonce` query parameter. Pass a new
                value, such as the time the file last changed, to bypass a cached copy.

        Returns:
            For each path, its signed URL or the error that prevented it.
        """
        url_query = _url_query(download, cache_nonce)

        body = CreateSignedUrlsBody(
            download=download,
            expiresIn=expires_in,
            paths=[_normalize_object_key(path) for path in paths],
        )
        response = yield JSONRequest(
            method="POST",
            path=["object", "sign", self.id],
            body=body,
        )
        return self._parse_signed_urls(response, url_query)

    def get_public_url(
        self,
        path: str,
        download: bool | str | None = None,
        transform: TransformOptions | None = None,
        *,
        cache_nonce: str | None = None,
    ) -> str:
        """
        Builds the URL of a file in a public bucket, without sending a request.

        Args:
            path: file path, including the path and file name. For example `folder/image.png`.
            download: `True` makes the URL download the file instead of showing it, and a
                file name does so under that name.
            transform: How to transform an image before it is served.
            cache_nonce: Appended to the URL as the `cacheNonce` query parameter. Pass a new
                value, such as the time the file last changed, to bypass a cached copy.

        Returns:
            The public URL of the file.
        """
        url_query = _url_query(download, cache_nonce)

        render_path = ["render", "image"] if transform else ["object"]
        transformation = transform_to_dict(transform) if transform else {}

        path_parts = relative_path_to_parts(path)
        url = (
            self.base_url.joinpath(*render_path, "public", self.id, *path_parts)
            .with_query(url_query.as_query())
            .extend_query(transformation)
        )
        return str(url)

    @handle_http_io
    def move(
        self,
        from_path: str,
        to_path: str,
        *,
        destination_bucket: str | None = None,
    ) -> HttpMethod[MessageResponse]:
        """
        Moves an existing file, optionally renaming it at the same time.

        Args:
            from_path: The original file path, including the current file name. For example `folder/image.png`.
            to_path: The new file path, including the new file name. For example `folder/image-copy.png`.
            destination_bucket: The bucket to move the file to. Defaults to this bucket.

        Returns:
            The message the server answers with.
        """
        response = yield JSONRequest(
            method="POST",
            path=["object", "move"],
            body=self._destination_body(
                _normalize_object_key(from_path),
                _normalize_object_key(to_path),
                destination_bucket,
            ),
        )
        return _validate_model(response, MessageResponse)

    @handle_http_io
    def copy(
        self,
        from_path: str,
        to_path: str,
        *,
        destination_bucket: str | None = None,
        upsert: bool = False,
        copy_metadata: bool = True,
        metadata: dict[str, Any] | None = None,
        cache_control: str | None = None,
        content_type: str | None = None,
        content_encoding: str | None = None,
    ) -> HttpMethod[UploadResponse]:
        """
        Copies an existing file to a new path.

        Args:
            from_path: The original file path, including the current file name. For example `folder/image.png`.
            to_path: The new file path, including the new file name. For example `folder/image-copy.png`.
            destination_bucket: The bucket to copy the file to. Defaults to this bucket.
            upsert: Whether to overwrite the file at `to_path` if it already exists.
            copy_metadata: Whether the copy keeps the metadata of the original file. Set it to
                `False` to replace the custom metadata with `metadata` and to
                override the file metadata given below.
            metadata: The custom metadata of the copy. Requires `copy_metadata=False`.
            cache_control: The `Cache-Control` of the copy. A number of seconds, as in
                `upload()`, is sent as `max-age=<seconds>`; any other value, like
                `no-cache`, is sent as given. Requires `copy_metadata=False`.
            content_type: The `Content-Type` of the copy. Requires `copy_metadata=False`.
            content_encoding: The `Content-Encoding` of the copy. An empty string clears it. It
                changes the metadata only, not the bytes of the file. Requires
                `copy_metadata=False` and Supabase Storage v1.80.0 or newer.

        Returns:
            The object written by the copy.

        Raises:
            ValueError: If `metadata`, `cache_control`, `content_type` or
                `content_encoding` is given without `copy_metadata=False`.
        """
        file_metadata = {
            key: value
            for key, value in (
                ("cacheControl", _cache_control_header(cache_control)),
                ("mimetype", content_type),
                ("contentEncoding", content_encoding),
            )
            if value is not None
        }
        if copy_metadata and (metadata is not None or file_metadata):
            raise ValueError(
                "metadata, cache_control, content_type and content_encoding "
                "require copy_metadata=False"
            )

        headers = Headers.empty().set("x-upsert", _bool_header(upsert))
        to_key = _normalize_object_key(to_path)
        body = self._destination_body(
            _normalize_object_key(from_path), to_key, destination_bucket
        )
        if not copy_metadata:
            body["copyMetadata"] = False
            if file_metadata:
                body["metadata"] = file_metadata
            if metadata is not None:
                headers = headers.set(
                    "x-metadata",
                    base64.b64encode(JSONParser.dump_json(metadata)).decode("ascii"),
                )

        response = yield JSONRequest(
            method="POST",
            path=["object", "copy"],
            body=body,
            headers=headers,
        )
        return _parse_upload_response(response, to_key)

    def _destination_body(
        self, from_key: str, to_key: str, destination_bucket: str | None
    ) -> dict[str, JSON]:
        body: dict[str, JSON] = {
            "bucketId": self.id,
            "sourceKey": from_key,
            "destinationKey": to_key,
        }
        if destination_bucket is not None:
            body["destinationBucket"] = destination_bucket
        return body

    @handle_http_io
    def remove(self, paths: list[str]) -> HttpMethod[list[FileObject]]:
        """
        Deletes files within the same bucket

        Args:
            paths: An array or list of files to be deletes, including the path and file name. For example [`folder/image.png`].

        Returns:
            The deleted files.
        """
        response = yield JSONRequest(
            method="DELETE",
            path=["object", self.id],
            body={"prefixes": [_normalize_object_key(path) for path in paths]},
        )
        return _validate_adapter(response, FileObjectsAdapter)

    @handle_http_io
    def info(
        self,
        path: str,
    ) -> HttpMethod[FileObject]:
        """
        Lists info for a particular file.

        Args:
            path: The path to the file.

        Returns:
            The information of the file.
        """
        path_parts: tuple[str, ...] = relative_path_to_parts(path)  # split paths by /
        response = yield EmptyRequest(
            method="GET",
            path=["object", "info", self.id, *path_parts],
        )
        return _validate_model(response, FileObject)

    @handle_http_io
    def exists(
        self,
        path: str,
    ) -> HttpMethod[bool]:
        """
        Returns True if the file exists, False if it does not.

        Args:
            path: The path to the file.

        Returns:
            Whether the file exists.

        Raises:
            StorageApiError: For any other error, such as an invalid token or a
                missing bucket.
        """
        response = yield EmptyRequest(
            method="GET",
            path=["object", "info", self.id, *relative_path_to_parts(path)],
        )
        if response.is_success:
            return True
        error = parse_api_error(response)
        if error.code == "NoSuchKey":
            return False
        raise error

    @handle_http_io
    def list(
        self,
        prefix: str | None = None,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        with_delimiter: bool | None = None,
        sort_by: SortBy | None = None,
    ) -> HttpMethod[ListResult]:
        """
        Lists one page of the objects in the bucket.

        Needs Supabase Storage v1.19.0 or newer.

        Args:
            prefix: The start of the object keys to list. It is sent as given: `photos`
                also selects `photos-old/a.png`, while `photos/` selects the keys
                under that folder.
            limit: The page size. The server default and maximum are 1000.
            cursor: The `nextCursor` of the previous page. Pass it with the same
                arguments as the first page.
            with_delimiter: When `True`, lists one level: the keys below the next `/` after
                `prefix` are collapsed into `folders`, named by their full prefix
                ending in `/`. Otherwise every key at every depth is listed and
                `folders` is empty.
            sort_by: The column and order to sort by. Defaults to `name` ascending.

        Returns:
            One page of the objects and folders, with the cursor of the next page.
        """
        body = ListBody(
            prefix=prefix,
            limit=limit,
            cursor=cursor,
            with_delimiter=with_delimiter,
            sortBy=sort_by,
        )
        response = yield JSONRequest(
            method="POST",
            path=["object", "list-v2", self.id],
            body=body,
        )
        return _validate_model(response, ListResult)

    @overload
    def pages(
        self: StorageFileApiClient[SyncHttpIO],
        prefix: str | None = None,
        *,
        limit: int | None = None,
        with_delimiter: bool | None = None,
        sort_by: SortBy | None = None,
    ) -> Iterator[ListResult]: ...

    @overload
    def pages(
        self: StorageFileApiClient[AsyncHttpIO],
        prefix: str | None = None,
        *,
        limit: int | None = None,
        with_delimiter: bool | None = None,
        sort_by: SortBy | None = None,
    ) -> AsyncIterator[ListResult]: ...

    def pages(
        self: StorageFileApiClient[Any],
        prefix: str | None = None,
        *,
        limit: int | None = None,
        with_delimiter: bool | None = None,
        sort_by: SortBy | None = None,
    ) -> Iterator[ListResult] | AsyncIterator[ListResult]:
        """
        Lists the objects in the bucket page by page, following the cursor of
        each page.

        Iterate with `for` on the sync client and with `async for` on the async
        client. Each page is fetched only when the loop reaches it. The
        parameters are those of `list`. Raises `StorageException` when a page
        returns the cursor it was fetched with, instead of fetching it forever.
        """
        options = _ListOptions(prefix, limit, with_delimiter, sort_by)
        if isinstance(self.executor, AsyncHttpIO):
            return _async_pages(self, options)
        return _sync_pages(self, options)

    def _download_request(
        self,
        path: str,
        transform: TransformOptions | None,
        query_params: dict[str, str] | None,
        byte_range: str | None,
        if_match: str | None,
        cache_nonce: str | None,
    ) -> EmptyRequest:
        render_path: list[str] = ["object"]
        params = (
            URLQuery.from_mapping(query_params) if query_params else URLQuery.empty()
        )
        if transform:
            params = params.merge(URLQuery.from_mapping(transform_to_dict(transform)))
            render_path = ["render", "image", "authenticated"]
        if cache_nonce:
            params = params.override("cacheNonce", cache_nonce)
        path_parts: tuple[str, ...] = relative_path_to_parts(path)
        headers = Headers.empty()
        if byte_range is not None:
            headers = headers.set("Range", byte_range).set(
                "Accept-Encoding", "identity"
            )
        if if_match is not None:
            headers = headers.set("If-Match", if_match)
        return EmptyRequest(
            method="GET",
            path=[*render_path, self.id, *path_parts],
            query=params,
            headers=headers,
        )

    @overload
    def download(
        self: StorageFileApiClient[SyncHttpIO],
        path: str,
        transform: TransformOptions | None = None,
        query_params: dict[str, str] | None = None,
        *,
        offset: int = 0,
        length: int | None = None,
        if_match: str | None = None,
        cache_nonce: str | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> bytes: ...

    @overload
    def download(
        self: StorageFileApiClient[AsyncHttpIO],
        path: str,
        transform: TransformOptions | None = None,
        query_params: dict[str, str] | None = None,
        *,
        offset: int = 0,
        length: int | None = None,
        if_match: str | None = None,
        cache_nonce: str | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> Coroutine[Any, Any, bytes]: ...

    def download(
        self: StorageFileApiClient[Any],
        path: str,
        transform: TransformOptions | None = None,
        query_params: dict[str, str] | None = None,
        *,
        offset: int = 0,
        length: int | None = None,
        if_match: str | None = None,
        cache_nonce: str | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> bytes | Coroutine[Any, Any, bytes]:
        """
        Downloads a file into memory. Use `download_stream` for a file
        too large to hold in memory.

        A byte range, from `offset` or of `length` bytes, raises
        `StorageRangeIgnoredError` when the server answers with the whole file
        instead, as a cache that ignores the range does. Use
        `download_stream` to accept the whole file in that case.

        Args:
            path: The file path to be downloaded, including the path and file name. For example `folder/image.png`.
            transform: How to transform an image before it is downloaded.
            query_params: Extra query parameters sent with the request.
            offset: The first byte to download, counted from 0. Pass the size of a
                partial file to resume it.
            length: How many bytes to download from `offset`. Defaults to every byte
                up to the end of the file. A range that ends past the end of the
                file stops at its end.
            if_match: The `etag` of an earlier download of the file. When the file
                changed since, the server answers with HTTP 412 and the call raises
                `StorageApiError` with the code `PreconditionFailed`, so a resumed
                download never mixes the bytes of two versions.
            cache_nonce: Appended to the request URL as the `cacheNonce` query parameter. Pass a new
                value, such as the time the file last changed, to bypass a cached copy.
            on_progress: Called with the bytes received so far and the total, or None when
                the total is not known, as the body arrives. It restarts from 0
                when the download is retried.

        Returns:
            The bytes of the file, or of the requested range.
        """
        byte_range = _byte_range(offset, length)
        request = self._download_request(
            path, transform, query_params, byte_range, if_match, cache_nonce
        )
        if isinstance(self.executor, AsyncHttpIO):
            return _async_read(
                self.executor,
                self.base_url,
                self.default_headers,
                request,
                byte_range,
                on_progress,
            )
        return _sync_read(
            self.executor,
            self.base_url,
            self.default_headers,
            request,
            byte_range,
            on_progress,
        )

    @overload
    def download_stream(
        self: StorageFileApiClient[SyncHttpIO],
        path: str,
        transform: TransformOptions | None = None,
        query_params: dict[str, str] | None = None,
        *,
        offset: int = 0,
        length: int | None = None,
        if_match: str | None = None,
        cache_nonce: str | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> AbstractContextManager[StorageDownload]: ...

    @overload
    def download_stream(
        self: StorageFileApiClient[AsyncHttpIO],
        path: str,
        transform: TransformOptions | None = None,
        query_params: dict[str, str] | None = None,
        *,
        offset: int = 0,
        length: int | None = None,
        if_match: str | None = None,
        cache_nonce: str | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> AbstractAsyncContextManager[AsyncStorageDownload]: ...

    def download_stream(
        self: StorageFileApiClient[Any],
        path: str,
        transform: TransformOptions | None = None,
        query_params: dict[str, str] | None = None,
        *,
        offset: int = 0,
        length: int | None = None,
        if_match: str | None = None,
        cache_nonce: str | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> (
        AbstractContextManager[StorageDownload]
        | AbstractAsyncContextManager[AsyncStorageDownload]
    ):
        """
        Downloads a file and reads its body as it arrives, without holding it
        in memory.

        Entering the returned context sends the request and gives the
        download once the response head arrived, with its status and headers.
        An error response raises the same `StorageApiError` as `download`.
        Leaving the context closes the connection.

        A byte range, from `offset` or of `length` bytes, is answered with
        status 206 and a `Content-Range` header, or with status 200 and the
        whole file when the server or a cache ignores the range. Pass
        `resume=True` to `write_to` to continue a partial file, and the
        `etag` of the first download as `if_match`, so a file that changed
        since raises instead of being appended to:

        ```python
        with client.from_("videos").download_stream("intro.mp4") as download:
            download.write_to("intro.mp4")

        async with client.from_("videos").download_stream("intro.mp4") as download:
            async for chunk in download:
                ...

        partial = Path("intro.mp4")
        offset = partial.stat().st_size if partial.exists() else 0
        with client.from_("videos").download_stream(
            "intro.mp4", offset=offset, if_match=saved_etag
        ) as download:
            download.write_to(partial, resume=True)
        ```

        Args:
            path: The file path to be downloaded, including the path and file name. For example `folder/image.png`.
            transform: How to transform an image before it is downloaded.
            query_params: Extra query parameters sent with the request.
            offset: The first byte to download, counted from 0. Pass the size of a
                partial file to resume it.
            length: How many bytes to download from `offset`. Defaults to every byte
                up to the end of the file. A range that ends past the end of the
                file stops at its end.
            if_match: The `etag` of an earlier download of the file. When the file
                changed since, the server answers with HTTP 412 and the call raises
                `StorageApiError` with the code `PreconditionFailed`, so a resumed
                download never mixes the bytes of two versions.
            cache_nonce: Appended to the request URL as the `cacheNonce` query parameter. Pass a new
                value, such as the time the file last changed, to bypass a cached copy.
            on_progress: Called with the bytes of the body read so far and the total, or
                None when the total is not known, as the body is read.

        Returns:
            A context manager that sends the request when entered and gives the download.
        """
        byte_range = _byte_range(offset, length)
        request = self._download_request(
            path, transform, query_params, byte_range, if_match, cache_nonce
        )
        if isinstance(self.executor, AsyncHttpIO):
            return _async_download(
                self.executor, self.base_url, self.default_headers, request, on_progress
            )
        return _sync_download(
            self.executor, self.base_url, self.default_headers, request, on_progress
        )

    def _upload_or_update(
        self,
        method: Literal["POST", "PUT"],
        path: tuple[str, ...],
        file: UploadBody,
        cache_control: str,
        content_type: str,
        upsert: bool | None,
        metadata: dict[str, Any] | None,
        headers: dict[str, str] | None,
        on_progress: ProgressCallback | None,
    ) -> HttpMethod[UploadResponse]:
        http_headers = _upload_headers(
            content_type, cache_control, metadata, upsert, headers
        )
        with _upload_content(file, on_progress) as content:
            response = yield BytesRequest(
                method=method,
                path=["object", self.id, *path],
                body=content,
                headers=http_headers,
            )

        return _parse_upload_response(response, "/".join(path))

    @handle_http_io
    def upload(
        self,
        path: str,
        file: UploadBody,
        cache_control: str = "3600",
        content_type: str = "text/plain;charset=UTF-8",
        upsert: bool = False,
        metadata: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        *,
        on_progress: ProgressCallback | None = None,
    ) -> HttpMethod[UploadResponse]:
        """
        Uploads a file to an existing bucket.

        Args:
            path: The relative file path including the bucket ID. Should be of the format `bucket/folder/subfolder/filename.png`.
                The bucket must already exist before attempting to upload.
            file: What to upload: the bytes, the path of a file, a binary file or an
                iterator over the bytes. A file or an iterator is streamed instead
                of read into memory first. A request whose body is an iterator, or
                a file that cannot seek, is never retried.
            cache_control: The number of seconds the file is cached in the browser and
                the Supabase CDN, sent as `Cache-Control: max-age=<seconds>`.
            content_type: The `Content-Type` the file is stored with.
            upsert: Whether to overwrite the file if it already exists.
            metadata: Custom metadata stored with the file, a JSON object.
            headers: Extra headers sent with the request.
            on_progress: Called with the bytes sent so far and the total, or None when the
                total is not known, as the body is sent. It restarts from 0 when
                the body is sent again.

        Returns:
            The uploaded object.
        """
        path_parts = relative_path_to_parts(path)
        return self._upload_or_update(
            method="POST",
            path=path_parts,
            file=file,
            cache_control=cache_control,
            content_type=content_type,
            upsert=upsert,
            metadata=metadata,
            headers=headers,
            on_progress=on_progress,
        )

    @overload
    def resumable_upload(
        self: StorageFileApiClient[SyncHttpIO],
        path: str,
        file: ResumableUploadSource,
        *,
        content_type: str = "text/plain;charset=UTF-8",
        cache_control: str = "3600",
        upsert: bool = False,
        metadata: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        store: MutableMapping[str, str] | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> ResumableUpload: ...

    @overload
    def resumable_upload(
        self: StorageFileApiClient[AsyncHttpIO],
        path: str,
        file: ResumableUploadSource,
        *,
        content_type: str = "text/plain;charset=UTF-8",
        cache_control: str = "3600",
        upsert: bool = False,
        metadata: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        store: MutableMapping[str, str] | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> AsyncResumableUpload: ...

    def resumable_upload(
        self: StorageFileApiClient[Any],
        path: str,
        file: ResumableUploadSource,
        *,
        content_type: str = "text/plain;charset=UTF-8",
        cache_control: str = "3600",
        upsert: bool = False,
        metadata: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        store: MutableMapping[str, str] | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> ResumableUpload | AsyncResumableUpload:
        """
        Prepares an upload sent in chunks with the tus protocol, which can be
        paused, continued after a failure, and continued by another process.
        Nothing is sent until `run` is called on the returned upload.

        ```python
        upload = client.from_("videos").resumable_upload(
            "holiday.mp4", "holiday.mp4", content_type="video/mp4"
        )
        response = upload.run()
        ```

        Args:
            path: The file path, including the file name. For example `folder/video.mp4`.
            file: What to upload: the bytes, the path of a file, or a binary file
                that can seek. A file is read one chunk at a time.
            content_type: The `Content-Type` the file is stored with.
            cache_control: The number of seconds the file is cached in the browser and
                the Supabase CDN.
            upsert: Whether to overwrite the file if it already exists.
            metadata: Custom metadata stored with the file, a JSON object.
            headers: Extra headers sent with every request of the upload.
            chunk_size: The bytes sent per request. Hosted Supabase only accepts the
                default, 6 MiB. Change it to match a self-hosted server configured
                with another `TUS_PART_SIZE`.
            store: Where the URL of the upload is kept under its fingerprint, so that
                a later `resumable_upload` of the same file to the same path
                continues it instead of starting over. Pass a `dict` to share it
                within the process, or a `shelve.Shelf` to continue after a
                restart. Without one, only the returned upload can continue.
            on_progress: Called with the bytes the server holds, plus those of the chunk in
                flight, and the size of the file. It can go down when a chunk is
                sent again.

        Returns:
            The upload, which sends nothing until `run` is called.
        """
        options: dict[str, Any] = {
            "path": _normalize_object_key(path),
            "source": file,
            "content_type": content_type,
            "cache_control": cache_control,
            "upsert": upsert,
            "metadata": metadata,
            "headers": headers,
            "chunk_size": chunk_size,
            "store": store,
            "on_progress": on_progress,
        }
        if isinstance(self.executor, AsyncHttpIO):
            return AsyncResumableUpload(bucket=self, **options)
        return ResumableUpload(bucket=self, **options)

    @handle_http_io
    def update(
        self,
        path: str,
        file: UploadBody,
        cache_control: str = "3600",
        content_type: str = "text/plain;charset=UTF-8",
        metadata: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        *,
        on_progress: ProgressCallback | None = None,
    ) -> HttpMethod[UploadResponse]:
        """
        Replaces an existing file, taking the same arguments as `upload`.
        """
        path_parts = relative_path_to_parts(path)
        return self._upload_or_update(
            method="PUT",
            path=path_parts,
            file=file,
            cache_control=cache_control,
            content_type=content_type,
            upsert=None,
            metadata=metadata,
            headers=headers,
            on_progress=on_progress,
        )
