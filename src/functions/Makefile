tests: pytest

pytest:
	uv run --package supabase_functions pytest --cov=./ --cov-report=xml --cov-report=html -vv

unasync:
	uv run --package supabase_functions run-unasync.py

build-sync: unasync
	sed -i '0,/SyncMock, /{s/SyncMock, //}' tests/_sync/test_function_client.py
	sed -i 's/SyncMock/Mock/g' tests/_sync/test_function_client.py
	sed -i 's/SyncClient/Client/g' src/supabase_functions/_sync/functions_client.py tests/_sync/test_function_client.py
