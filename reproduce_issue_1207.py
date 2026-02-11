import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from postgrest._async.request_builder import AsyncMaybeSingleRequestBuilder, AsyncSingleRequestBuilder
from postgrest._sync.request_builder import SyncMaybeSingleRequestBuilder, SyncSingleRequestBuilder
from postgrest.exceptions import APIError
from postgrest.base_request_builder import RequestConfig
from httpx import Headers, QueryParams
from yarl import URL

# Helper to create a dummy request config
def make_req_config():
    return RequestConfig(
        session=MagicMock(),
        path=URL("/path"),
        http_method="GET",
        headers=Headers(),
        params=QueryParams(),
        auth=None,
        json={}
    )

async def test_async_maybe_single():
    print("\n--- Testing Async maybe_single ---")
    
    # Case 1: Success but empty list (200 OK [])
    print("[Async] Case 1: Success empty list")
    
    # Mock SingleAPIResponse returned by SingleRequestBuilder
    mock_response = MagicMock()
    mock_response.data = [] # Empty list
    
    # Patch AsyncSingleRequestBuilder.execute
    with patch("postgrest._async.request_builder.AsyncSingleRequestBuilder.execute", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = mock_response
        
        builder = AsyncMaybeSingleRequestBuilder(make_req_config())
        result = await builder.execute()
        
        if result is None:
            print("SUCCESS Case 1: Returned None")
        else:
            print(f"FAILURE Case 1: Returned {result}")

    # Case 2: Error PGRST116 (0 rows)
    print("\n[Async] Case 2: Error PGRST116 (0 rows)")
    error_dict = {"code": "PGRST116", "details": "The result contains 0 rows", "message": "msg"}
    api_error = APIError(error_dict)
    
    with patch("postgrest._async.request_builder.AsyncSingleRequestBuilder.execute", new_callable=AsyncMock) as mock_exec:
        mock_exec.side_effect = api_error
        
        builder = AsyncMaybeSingleRequestBuilder(make_req_config())
        try:
            result = await builder.execute()
            if result is None:
                print("SUCCESS Case 2: Returned None")
            else:
                 print(f"FAILURE Case 2: Returned {result}")
        except Exception as e:
            print(f"FAILURE Case 2: Raised exception {e}")

    # Case 3: Error PGRST116 (Variation '0 rows returned')
    print("\n[Async] Case 3: Error PGRST116 (Variation)")
    error_dict_var = {"code": "PGRST116", "details": "0 rows returned", "message": "msg"}
    api_error_var = APIError(error_dict_var)
    
    with patch("postgrest._async.request_builder.AsyncSingleRequestBuilder.execute", new_callable=AsyncMock) as mock_exec:
        mock_exec.side_effect = api_error_var
        
        builder = AsyncMaybeSingleRequestBuilder(make_req_config())
        try:
            result = await builder.execute()
            if result is None:
                print("SUCCESS Case 3: Returned None")
            else:
                 print(f"FAILURE Case 3: Returned {result}")
        except Exception as e:
             print(f"FAILURE Case 3: Raised exception {e}")

    # Case 4: Other Error (Should raise)
    print("\n[Async] Case 4: Other Error (should raise)")
    other_error = APIError({"code": "PGRST116", "details": "The result contains 2 rows", "message": "msg"})
    
    with patch("postgrest._async.request_builder.AsyncSingleRequestBuilder.execute", new_callable=AsyncMock) as mock_exec:
        mock_exec.side_effect = other_error
        
        builder = AsyncMaybeSingleRequestBuilder(make_req_config())
        try:
            await builder.execute()
            print("FAILURE Case 4: Did not raise exception")
        except APIError:
            print("SUCCESS Case 4: Raised APIError")

def test_sync_maybe_single():
    print("\n--- Testing Sync maybe_single ---")
    
    # Case 1: Success empty list
    print("[Sync] Case 1: Success empty list")
    mock_response = MagicMock()
    mock_response.data = []
    
    with patch("postgrest._sync.request_builder.SyncSingleRequestBuilder.execute") as mock_exec:
        mock_exec.return_value = mock_response
        
        builder = SyncMaybeSingleRequestBuilder(make_req_config())
        result = builder.execute()
        
        if result is None:
            print("SUCCESS Case 1: Returned None")
        else:
             print(f"FAILURE Case 1: Returned {result}")

    # Case 3: Error PGRST116 (Variation)
    print("\n[Sync] Case 3: Error PGRST116 (Variation)")
    error_dict_var = {"code": "PGRST116", "details": "0 rows returned", "message": "msg"}
    api_error_var = APIError(error_dict_var)
    
    with patch("postgrest._sync.request_builder.SyncSingleRequestBuilder.execute") as mock_exec:
        mock_exec.side_effect = api_error_var
        
        builder = SyncMaybeSingleRequestBuilder(make_req_config())
        try:
            result = builder.execute()
            if result is None:
                print("SUCCESS Case 3: Returned None")
            else:
                 print(f"FAILURE Case 3: Returned {result}")
        except Exception as e:
             print(f"FAILURE Case 3: Raised exception {e}")


if __name__ == "__main__":
    try:
        test_sync_maybe_single()
        asyncio.run(test_async_maybe_single())
    except ImportError as e:
        print(f"Import Error: {e}")
