help::
	@echo "Available commands"
	@echo "  help           -- (default) print this message"

start-infra:
	supabase --workdir infra start -x studio,gotrue,postgrest,mailpit,realtime,edge-runtime,logflare,vector,supavisor
help::
	@echo "  start-infra    -- start containers for tests"

stop-infra:
	supabase --workdir infra stop
help::
	@echo "  stop-infra     -- stop containers for tests"

tests: mypy pytest
help::
	@echo "  tests          -- run all tests for storage3"

mypy:
	uv run --package storage3 mypy src/storage3 tests
help::
	@echo "  mypy           -- run mypy on storage3"

pytest: start-infra
	uv run --package storage3 pytest --cov=./ --cov-report=xml --cov-report=html -vv
help::
	@echo "  pytest         -- run pytest on storage3"

clean:
	rm -rf htmlcov .pytest_cache .mypy_cache .ruff_cache
	rm -f .coverage coverage.xml
help::
	@echo "  clean          -- clean intermediary files"

build:
	uv build --package storage3
help::
	@echo "  build          -- invoke uv build on storage3 package"
