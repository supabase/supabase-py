start-infra:
	supabase --workdir infra start -x studio,gotrue,postgrest,mailpit,realtime,edge-runtime,logflare,vector,supavisor

stop-infra:
	supabase --workdir infra stop

tests: pytest

pytest: start-infra
	uv run --package storage3 pytest --cov=./ --cov-report=xml --cov-report=html -vv

build-sync:
	uv run --package storage3 run-unasync.py
	sed -i '0,/SyncMock, /{s/SyncMock, //}' tests/_sync/test_bucket.py tests/_sync/test_client.py
	sed -i 's/SyncMock/Mock/g' tests/_sync/test_bucket.py tests/_sync/test_client.py
	sed -i 's/SyncClient/Client/g' storage3/_sync/client.py storage3/_sync/bucket.py storage3/_sync/file_api.py tests/_sync/test_bucket.py tests/_sync/test_client.py
	sed -i 's/self\.session\.aclose/self\.session\.close/g' storage3/_sync/client.py

clean:
	rm -rf htmlcov .pytest_cache .mypy_cache .ruff_cache
	rm -f .coverage coverage.xml

build:
	uv build --package storage3
