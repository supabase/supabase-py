#!/usr/bin/env python3
"""Script to clean up test vector buckets from Supabase.

This script lists all vector buckets and deletes those that match the test bucket pattern.

Usage:
    python cleanup_buckets.py          # Interactive mode
    python cleanup_buckets.py --yes     # Non-interactive mode (auto-confirm)
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from storage3 import AsyncStorageClient

# Load environment variables
tests_dir = Path(__file__).parent.parent
tests_env_local = tests_dir / "tests.env.local"
tests_env = tests_dir / "tests.env"

if tests_env_local.exists():
    load_dotenv(dotenv_path=str(tests_env_local))
elif tests_env.exists():
    load_dotenv(dotenv_path=str(tests_env))


async def cleanup_test_buckets(auto_confirm: bool = False) -> None:
    """Clean up all test vector buckets.
    
    Args:
        auto_confirm: If True, skip confirmation prompt and delete automatically.
    """
    url = os.environ.get("SUPABASE_TEST_URL")
    key = os.environ.get("SUPABASE_TEST_KEY")

    if not url or not key:
        print("Error: SUPABASE_TEST_URL and SUPABASE_TEST_KEY must be set")
        sys.exit(1)

    async with AsyncStorageClient(
        url,
        {
            "apiKey": key,
            "Authorization": f"Bearer {key}",
        },
    ) as client:
        client.session.timeout = None
        vectors_client = client.vectors()

        # List all buckets
        print("Fetching all vector buckets...")
        response = await vectors_client.list_buckets()
        buckets = response.vectorBuckets

        if not buckets:
            print("No vector buckets found.")
            return

        print(f"Found {len(buckets)} vector bucket(s)")

        # Filter test buckets (those starting with "test-")
        test_buckets = [
            bucket for bucket in buckets if bucket.vectorBucketName.startswith("test-")
        ]

        if not test_buckets:
            print("No test buckets found to clean up.")
            return

        print(f"\nFound {len(test_buckets)} test bucket(s) to clean up:")
        for bucket in test_buckets:
            print(f"  - {bucket.vectorBucketName}")

        # Confirm deletion
        if not auto_confirm:
            confirm = input("\nDelete these buckets? (yes/no): ").strip().lower()
            if confirm != "yes":
                print("Cancelled.")
                return
        else:
            print("\nAuto-confirming deletion (--yes flag)...")

        # Delete each test bucket
        deleted_count = 0
        failed_count = 0

        for bucket in test_buckets:
            bucket_name = bucket.vectorBucketName
            try:
                # First, delete all indexes in the bucket
                bucket_scope = vectors_client.from_(bucket_name)
                indexes_response = await bucket_scope.list_indexes()
                for index in indexes_response.indexes:
                    try:
                        await bucket_scope.delete_index(index.indexName)
                        print(f"  Deleted index: {index.indexName}")
                    except Exception as e:
                        print(f"  Warning: Failed to delete index {index.indexName}: {e}")

                # Then delete the bucket
                await vectors_client.delete_bucket(bucket_name)
                print(f"✓ Deleted bucket: {bucket_name}")
                deleted_count += 1
            except Exception as e:
                print(f"✗ Failed to delete bucket {bucket_name}: {e}")
                failed_count += 1

        print(f"\nCleanup complete: {deleted_count} deleted, {failed_count} failed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Clean up test vector buckets from Supabase"
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Auto-confirm deletion without prompting",
    )
    args = parser.parse_args()

    asyncio.run(cleanup_test_buckets(auto_confirm=args.yes))

