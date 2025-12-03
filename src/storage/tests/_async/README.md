# Vector Storage Tests

This directory contains integration tests for the vector storage functionality.

## Setup

1. Copy `tests.env.example` to `tests.env.local`:
   ```bash
   cp tests.env.example tests.env.local
   ```

2. Edit `tests.env.local` with your Supabase credentials:
   ```
   SUPABASE_TEST_KEY="your-key-here"
   SUPABASE_TEST_URL="https://your-project.supabase.co/storage/v1/"
   ```

## Running Tests

Run all vector tests:
```bash
uv run pytest tests/_async/test_vectors.py -v
```

Run a specific test:
```bash
uv run pytest tests/_async/test_vectors.py::test_create_vector_bucket -v
```

## Bucket Quota Management

Supabase has a limit of 10 vector buckets per project. The test suite includes several features to handle this:

### 1. Cleanup Script

Before running tests, clean up old test buckets:

```bash
uv run python tests/_async/cleanup_buckets.py
```

This script will:
- List all vector buckets
- Identify test buckets (those starting with "test-")
- Ask for confirmation
- Delete all indexes in each test bucket
- Delete the test buckets

### 2. Shared Bucket Fixture

Tests can use the `shared_vector_bucket` fixture for tests that don't require isolation:

```python
@pytest.mark.uses_shared_bucket
async def test_something(shared_vector_bucket: str):
    # Use shared_vector_bucket instead of creating a new one
    ...
```

The shared bucket is:
- Created once per test session
- Reused across multiple tests
- Automatically found if it already exists
- Not deleted after tests (for reuse)

### 3. Automatic Quota Handling

The `vector_bucket` fixture automatically:
- Checks bucket count before creating
- Skips tests if quota is exceeded (with helpful message)
- Suggests using `shared_vector_bucket` when quota is low
- Cleans up buckets after each test

## Test Fixtures

- `vector_bucket`: Creates an isolated bucket for each test (deleted after)
- `shared_vector_bucket`: Creates/reuses a shared bucket (session-scoped)
- `vector_index`: Creates an index in the isolated bucket
- `vector_index_shared`: Creates an index in the shared bucket
- `sample_vectors`: Sample vector data for testing
- `query_vector`: Sample query vector for similarity search

## Troubleshooting

### "Maximum number of buckets exceeded" error

1. Run the cleanup script:
   ```bash
   uv run python tests/_async/cleanup_buckets.py
   ```

2. Or manually delete buckets via Supabase dashboard

3. Use `shared_vector_bucket` fixture for tests that don't need isolation

### Tests are slow

- Tests run sequentially to avoid quota issues
- Consider using `shared_vector_bucket` for tests that don't need isolation
- Clean up buckets regularly

