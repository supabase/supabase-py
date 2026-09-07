from pathlib import Path

import unasync

rules = (
    unasync.Rule(
        fromdir="/_async/",
        todir="/_sync/",
        additional_replacements={
            "AsyncClient": "Client",
            "AsyncPostgrestClient": "SyncPostgrestClient",
            "async_postgrest_client": "sync_postgrest_client",
            "AsyncFilterRequestBuilder": "SyncFilterRequestBuilder",
            "AsyncSelectRequestBuilder": "SyncSelectRequestBuilder",
            "AsyncQueryRequestBuilder": "SyncQueryRequestBuilder",
            "AsyncSingleRequestBuilder": "SyncSingleRequestBuilder",
            "AsyncMaybeSingleRequestBuilder": "SyncMaybeSingleRequestBuilder",
            "AsyncExplainRequestBuilder": "SyncExplainRequestBuilder",
            "AsyncRPCFilterRequestBuilder": "SyncRPCFilterRequestBuilder",
            "AsyncRequestBuilder": "SyncRequestBuilder",
            "AsyncHTTPTransport": "HTTPTransport",
            "aclose": "close",
            "asyncio.sleep": "time.sleep",
            "import asyncio": "import time",
            "postgrest._async.request_builder.AsyncSelectRequestBuilder.execute": "postgrest._sync.request_builder.SyncSelectRequestBuilder.execute",
            "httpx._client.AsyncClient.request": "httpx._client.Client.request",
            "@pytest.mark.asyncio\n": "",
            "    @pytest.mark.asyncio\n": "",
        },
    ),
    unasync._DEFAULT_RULE,
)
paths = Path("src/postgrest").glob("**/*.py")
tests = Path("tests").glob("**/*.py")

files = [str(p) for p in list(paths) + list(tests)]

if __name__ == "__main__":
    unasync.unasync_files(files, rules=rules)
