help::
	@echo "Available commands"
	@echo "  help          -- (default) print this message"

# Exclude studio and heavyweight services; keep API, Auth, Realtime, DB.
EXCLUDE := studio,mailpit,edge-runtime,logflare,vector,supavisor,imgproxy,storage-api

start-infra:
	supabase start -x $(EXCLUDE)
help::
	@echo "  start-infra   -- start local Supabase (API, Auth, Realtime, DB)"

stop-infra:
	supabase stop
help::
	@echo "  stop-infra    -- stop local Supabase"

tests:
	uv run --package fastapi-realtime-rule-engine pytest tests/ --ignore=tests/e2e -v
help::
	@echo "  tests         -- run unit tests (no Supabase required)"

# E2E: requires Supabase to already be running (make start-infra first).
# Export credentials from supabase status and pass to pytest.
e2e:
	@eval "$$(supabase status -o env)" && \
	SUPABASE_URL=$$API_URL \
	SUPABASE_SERVICE_KEY=$$SERVICE_ROLE_KEY \
	SUPABASE_ANON_KEY=$$ANON_KEY \
	uv run --package fastapi-realtime-rule-engine pytest tests/e2e/ -v
help::
	@echo "  e2e           -- run E2E tests (requires: make start-infra first)"

clean:
	rm -rf htmlcov .pytest_cache .mypy_cache .ruff_cache
	rm -f .coverage coverage.xml
help::
	@echo "  clean         -- delete cache files"
