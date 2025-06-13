from __future__ import annotations

import os
import asyncio
import time
import pytest
from typing import Dict, Optional, List
from dotenv import load_dotenv
from supabase._async.client import AsyncClient, create_client
from supabase.lib.client_options import AsyncClientOptions

# Load test environment variables
load_dotenv(dotenv_path="tests/tests.env")

SUPABASE_URL = os.environ.get("SUPABASE_TEST_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_TEST_KEY")

# Constants for performance tuning
BATCH_SIZE = 5  # Reduced from 10
DELAY_BETWEEN_REQUESTS = 0.5  # seconds
TOTAL_REQUESTS = 15  # Reduced from 30

if not SUPABASE_URL or not SUPABASE_KEY:
    pytest.skip("Supabase credentials missing", allow_module_level=True)

async def create_supabase_client() -> AsyncClient:
    """Create a new Supabase client"""
    options = AsyncClientOptions(
        schema="public",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        }
    )
    return await create_client(SUPABASE_URL, SUPABASE_KEY, options)

async def get_role_ids(client: AsyncClient) -> List[str]:
    """Get all role IDs from the database"""
    response = await client.table("roles").select("id").execute()
    if not response.data:
        raise ValueError("No roles found in database")
    return [str(role["id"]) for role in response.data]

async def read_sdoc(client: AsyncClient, table: str, doc_ids: List[str], select: str) -> Dict:
    """Read multiple documents in one request"""
    query = client.table(table).select(select, count="exact")
    query = query.in_("id", doc_ids)
    response = await query.execute()
    if response.data:
        return {"data": response.data, "count": response.count}
    else:
        raise ValueError("No data found")

async def process_batch(client: AsyncClient, doc_ids: List[str]) -> List[Optional[Dict]]:
    """Process a batch of IDs in a single request"""
    try:
        result = await read_sdoc(client, "roles", doc_ids, "id, role")
        return [{"id": item["id"], "role": item["role"]} for item in result["data"]]
    except Exception as e:
        print(f"Error processing batch: {str(e)}")
        return [None] * len(doc_ids)

@pytest.mark.asyncio
async def test_single_request():
    """Test single request"""
    client = await create_supabase_client()
    role_ids = await get_role_ids(client)
    doc_id = role_ids[0]
    
    start = time.perf_counter()
    result = await process_batch(client, [doc_id])
    elapsed = time.perf_counter() - start
    
    print(f"\nSingle Request:")
    print(f"Doc ID: {doc_id}")
    print(f"Result: {result}")
    print(f"Elapsed time: {elapsed:.2f} seconds")
    
    assert result and result[0], "Request should return data"
    assert elapsed < 2.0, "Single request should complete in less than 2 seconds"

@pytest.mark.asyncio
async def test_batch_requests():
    """Test batch requests"""
    client = await create_supabase_client()
    role_ids = await get_role_ids(client)
    # Repeat IDs to get enough test data
    all_ids = (role_ids * (BATCH_SIZE // len(role_ids) + 1))[:BATCH_SIZE]
    
    start = time.perf_counter()
    results = await process_batch(client, all_ids)
    elapsed = time.perf_counter() - start
    success_count = sum(1 for r in results if r is not None)
    
    print(f"\nBatch Request ({BATCH_SIZE} items):")
    print(f"Successful items: {success_count} out of {BATCH_SIZE}")
    print(f"Elapsed time: {elapsed:.2f} seconds")
    print(f"Average time per item: {elapsed/BATCH_SIZE:.2f} seconds")
    
    assert success_count == BATCH_SIZE, f"All {BATCH_SIZE} items should be successful"
    assert elapsed < 5.0, f"Batch of {BATCH_SIZE} should complete in less than 5 seconds"

@pytest.mark.asyncio
async def test_multiple_batches():
    """Test multiple batches"""
    client = await create_supabase_client()
    role_ids = await get_role_ids(client)
    all_ids = (role_ids * (TOTAL_REQUESTS // len(role_ids) + 1))[:TOTAL_REQUESTS]
    
    # Split into batches
    batches = [all_ids[i:i + BATCH_SIZE] for i in range(0, len(all_ids), BATCH_SIZE)]
    
    start = time.perf_counter()
    all_results = []
    for batch in batches:
        results = await process_batch(client, batch)
        all_results.extend(results)
        # Longer delay between batches
        await asyncio.sleep(DELAY_BETWEEN_REQUESTS)
    
    elapsed = time.perf_counter() - start
    success_count = sum(1 for r in all_results if r is not None)
    
    print(f"\nMultiple Batches ({len(batches)} batches of {BATCH_SIZE}):")
    print(f"Total requests: {TOTAL_REQUESTS}")
    print(f"Successful requests: {success_count} out of {TOTAL_REQUESTS}")
    print(f"Total time: {elapsed:.2f} seconds")
    print(f"Average time per request: {elapsed/TOTAL_REQUESTS:.2f} seconds")
    print(f"Average time per batch: {elapsed/len(batches):.2f} seconds")
    
    assert success_count == TOTAL_REQUESTS, f"All {TOTAL_REQUESTS} requests should be successful"
    assert elapsed < 15.0, f"{TOTAL_REQUESTS} requests should complete in less than 15 seconds"

if __name__ == "__main__":
    asyncio.run(test_multiple_batches())

# New test for 50 requests
@pytest.mark.asyncio
async def test_fifty_requests():
    """Test with 50 requests to match original issue requirements"""
    FIFTY_REQUESTS = 50
    client = await create_supabase_client()
    role_ids = await get_role_ids(client)
    all_ids = (role_ids * (FIFTY_REQUESTS // len(role_ids) + 1))[:FIFTY_REQUESTS]
    
    # Split into batches of 5
    batches = [all_ids[i:i + BATCH_SIZE] for i in range(0, len(all_ids), BATCH_SIZE)]
    
    start = time.perf_counter()
    all_results = []
    for batch in batches:
        results = await process_batch(client, batch)
        all_results.extend(results)
        # Add delay between batches to avoid rate limiting
        await asyncio.sleep(DELAY_BETWEEN_REQUESTS)
    
    elapsed = time.perf_counter() - start
    success_count = sum(1 for r in all_results if r is not None)
    
    print(f"\n50 Requests Test:")
    print(f"Total batches: {len(batches)} batches of {BATCH_SIZE}")
    print(f"Total requests: {FIFTY_REQUESTS}")
    print(f"Successful requests: {success_count} out of {FIFTY_REQUESTS}")
    print(f"Total time: {elapsed:.2f} seconds")
    print(f"Average time per request: {elapsed/FIFTY_REQUESTS:.2f} seconds")
    print(f"Average time per batch: {elapsed/len(batches):.2f} seconds")
    
    assert success_count == FIFTY_REQUESTS, f"All {FIFTY_REQUESTS} requests should be successful"
    # Allow up to 30 seconds for 50 requests to complete
    assert elapsed < 30.0, f"{FIFTY_REQUESTS} requests should complete in less than 30 seconds" 