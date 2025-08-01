[doc("Lists all available commands")]
default:
    @just --list supabase

[doc("Run pytest in supabase")]
pytest:
    uv run --exact --package supabase pytest  --cov=./ --cov-report=xml --cov-report=html

[doc("Run unasync-cli in the supabase directory")]
unasync:
    uv run unasync src/supabase

[doc("Run fixups to generate the _sync directory from _async version")]
build_sync: unasync
    sed -i "" 's/asyncio.create_task(self.realtime.set_auth(access_token))//g' src/supabase/_sync/client.py
    sed -i "" 's/asynch/synch/g' src/supabase/_sync/auth_client.py
    sed -i "" 's/Async/Sync/g' src/supabase/_sync/auth_client.py
    sed -i "" 's/Async/Sync/g' src/supabase/_sync/client.py
    sed -i "" 's/create_async_client/create_client/g' tests/_sync/test_client.py
    sed -i "" 's/SyncClient/Client/g' tests/_sync/test_client.py
    sed -i "" 's/SyncHTTPTransport/HTTPTransport/g' tests/_sync/test_client.py
    sed -i "" 's/SyncMock/Mock/g' tests/_sync/test_client.py
