tests: pytest

pytest: start-infra
	uv run --package postgrest pytest --cov=./ --cov-report=xml -vv

start-infra:
	cd infra &&\
	docker compose down &&\
	docker compose up -d

clean-infra:
	cd infra &&\
	docker compose down --remove-orphans &&\
	docker system prune -a --volumes -f

stop-infra:
	cd infra &&\
	docker compose down --remove-orphans

clean:
	rm -rf htmlcov .pytest_cache .mypy_cache .ruff_cache
	rm -f .coverage coverage.xml

unasync:
	uv run unasync postgrest tests

build_sync: unasync
	sed -i 's/@pytest.mark.asyncio//g' tests/_sync/test_client.py
	sed -i 's/_async/_sync/g' tests/_sync/test_client.py
	sed -i 's/Async/Sync/g' src/postgrest/_sync/request_builder.py tests/_sync/test_client.py
	sed -i 's/_client\.SyncClient/_client\.Client/g' tests/_sync/test_client.py
	sed -i 's/SyncHTTPTransport/HTTPTransport/g' tests/_sync/**.py
	sed -i 's/SyncClient/Client/g' src/postgrest/_sync/**.py tests/_sync/**.py
	sed -i 's/self\.session\.aclose/self\.session\.close/g' src/postgrest/_sync/client.py

build:
	uv build --package supabase
