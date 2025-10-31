help::
	@echo "Available commands"
	@echo "  help           -- (default) print this message"

tests: ruff mypy pytest
help::
	@echo "  tests          -- run all tests for supabase_auth"

ruff:
	uv run ruff check tests src/supabase_auth
help::
	@echo "  ruff           -- run ruff checks"

pytest: start-infra
	uv run --package supabase_auth pytest --cov=./ --cov-report=xml --cov-report=html -vv

mypy:
	uv run --package supabase_auth mypy src/supabase_auth tests
help::
	@echo "  mypy           -- run mypy on supabase_auth"

start-infra:
	cd infra &&\
	docker compose down &&\
	docker compose up -d
	sleep 2
help::
	@echo "  start-infra    -- start containers for tests"

clean-infra:
	cd infra &&\
	docker compose down --remove-orphans &&\
	docker system prune -a --volumes -f
help::
	@echo "  clean-infra    -- delete all stored information about the containers"

stop-infra:
	cd infra &&\
	docker compose down --remove-orphans
help::
	@echo "  stop-infra     -- stop containers for tests"

sync-infra:
	uv run --package supabase_auth scripts/gh-download.py --repo=supabase/gotrue-js --branch=master --folder=infra
help::
	@echo "  sync-infra     -- update locked versions for test containers"

build-sync:
	uv run --package supabase_auth scripts/run-unasync.py
help::
	@echo "  build-sync     -- generate _sync from _async code"

clean:
	rm -rf htmlcov .pytest_cache .mypy_cache .ruff_cache
	rm -f .coverage coverage.xml
help::
	@echo "  clean          -- clean intermediary files"

build:
	uv build --package supabase_auth
help::
	@echo "  build          -- invoke uv build on supabase_auth package"
