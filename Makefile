install:
	poetry install

install_poetry:
	curl -sSL https://install.python-poetry.org | python -
	poetry install

tests: install tests_only tests_pre_commit

tests_pre_commit:
	poetry run pre-commit run --all-files

run_tests: tests

tests_only:
	poetry run pytest --cov=./ --cov-report=xml --cov-report=html -vv

build_sync:
	poetry run unasync supabase tests
	sed -i 's/asyncio.create_task(self.realtime.set_auth(access_token))//g' supabase/_sync/client.py
	sed -i 's/asynch/synch/g' supabase/_sync/auth_client.py
	sed -i 's/Async/Sync/g' supabase/_sync/auth_client.py
	sed -i 's/Async/Sync/g' supabase/_sync/client.py
	sed -i 's/create_async_client/create_client/g' tests/_sync/test_client.py
	sed -i 's/SyncClient/Client/gi' tests/_sync/test_client.py
	sed -i 's/SyncHTTPTransport/HTTPTransport/g' tests/_sync/test_client.py
	sed -i 's/SyncMock/Mock/g' tests/_sync/test_client.py
