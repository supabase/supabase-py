
import pytest
import respx
from httpx import Response
from postgrest import AsyncPostgrestClient, SyncPostgrestClient
from postgrest.exceptions import APIError

# --- Sync Tests using 'respx' ---

@respx.mock
def test_sync_maybe_single_empty_success():
    """
    Test SyncMaybeSingleRequestBuilder with a successful 200 OK empty response ([]).
    Should return None.
    """
    respx.get("https://example.com/table?select=*").mock(
        return_value=Response(200, json=[])
    )
    
    client = SyncPostgrestClient("https://example.com")
    result = client.from_("table").select("*").maybe_single().execute()
    
    assert result is None

@respx.mock
def test_sync_maybe_single_pgrst116_error():
    """
    Test SyncMaybeSingleRequestBuilder with a 406 Error (PGRST116).
    Should return None.
    """
    error_json = {
        "code": "PGRST116",
        "details": "The result contains 0 rows",
        "hint": None,
        "message": "JSON object requested, multiple (or no) rows returned"
    }
    respx.get("https://example.com/table?select=*").mock(
        return_value=Response(406, json=error_json)
    )
    
    client = SyncPostgrestClient("https://example.com")
    result = client.from_("table").select("*").maybe_single().execute()
    
    assert result is None

@respx.mock
def test_sync_maybe_single_pgrst116_error_variant():
    """
    Test SyncMaybeSingleRequestBuilder with a VARIANT 406 Error.
    Should return None.
    """
    error_json = {
        "code": "PGRST116",
        "details": "0 rows returned",
        "hint": None,
        "message": "JSON object requested, multiple (or no) rows returned"
    }
    respx.get("https://example.com/table?select=*").mock(
        return_value=Response(406, json=error_json)
    )
    
    client = SyncPostgrestClient("https://example.com")
    result = client.from_("table").select("*").maybe_single().execute()
    
    assert result is None


# --- Async Tests using 'respx' ---

@pytest.mark.asyncio
@respx.mock
async def test_async_maybe_single_empty_success():
    """
    Test AsyncMaybeSingleRequestBuilder with a successful 200 OK empty response ([]).
    Should return None.
    """
    respx.get("https://example.com/table?select=*").mock(
        return_value=Response(200, json=[])
    )
    
    async with AsyncPostgrestClient("https://example.com") as client:
        result = await client.from_("table").select("*").maybe_single().execute()
        assert result is None

@pytest.mark.asyncio
@respx.mock
async def test_async_maybe_single_pgrst116_error():
    """
    Test AsyncMaybeSingleRequestBuilder with a 406 Error (PGRST116).
    Should return None.
    """
    error_json = {
        "code": "PGRST116",
        "details": "The result contains 0 rows",
        "hint": None,
        "message": "JSON object requested, multiple (or no) rows returned"
    }
    respx.get("https://example.com/table?select=*").mock(
        return_value=Response(406, json=error_json)
    )
    
    async with AsyncPostgrestClient("https://example.com") as client:
        result = await client.from_("table").select("*").maybe_single().execute()
        assert result is None

@pytest.mark.asyncio
@respx.mock
async def test_async_maybe_single_other_error():
    """
    Test AsyncMaybeSingleRequestBuilder with a different error (should raise APIError).
    """
    error_json = {
        "code": "PGRST111",
        "details": "Some other error",
        "hint": None,
        "message": "Error details"
    }
    respx.get("https://example.com/table?select=*").mock(
        return_value=Response(400, json=error_json)
    )
    
    async with AsyncPostgrestClient("https://example.com") as client:
        with pytest.raises(APIError):
            await client.from_("table").select("*").maybe_single().execute()

@pytest.mark.asyncio
@respx.mock
async def test_async_maybe_single_head():
    """
    Test HEAD request with maybe_single.
    Should handle successful HEAD gracefully.
    """
    respx.head("https://example.com/table?select=*").mock(
        return_value=Response(200, headers={"Content-Range": "0-0/1"})
    )
    
    async with AsyncPostgrestClient("https://example.com") as client:
        result = await client.from_("table").select("*", head=True).maybe_single().execute()
        # HEAD returns no body. Our fix returns None if data is empty list.
        # Check if result is None or has empty data.
        assert result is None or result.data is None or result.data == []
 
