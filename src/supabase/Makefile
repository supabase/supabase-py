.PHONY: pytest pre-commit unasync build-sync tests

pytest:
	uv run --package --exact supabase pytest --cov=./ --cov-report=xml --cov-report=html -vv

pre-commit:
	uv run pre-commit run --all-files

unasync:
	uv run run-unasync.py

build-sync: unasync
	sed -i 's/asyncio.create_task(self.realtime.set_auth(access_token))//g' src/supabase/_sync/client.py
	sed -i 's/asynch/synch/g' src/supabase/_sync/auth_client.py
	sed -i 's/Async/Sync/g' src/supabase/_sync/auth_client.py
	sed -i 's/Async/Sync/g' src/supabase/_sync/client.py
	sed -i 's/create_async_client/create_client/g' tests/_sync/test_client.py
	sed -i 's/SyncClient/Client/gi' tests/_sync/test_client.py
	sed -i 's/SyncHTTPTransport/HTTPTransport/g' tests/_sync/test_client.py
	sed -i 's/SyncMock/Mock/g' tests/_sync/test_client.py

tests: pre-commit pytest
