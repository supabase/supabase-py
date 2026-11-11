help::
	@echo "Available commands"
	@echo "  help           -- (default) print this message"

tests: pyrefly pytest
help::
	@echo "  tests          -- run all tests for supabase_auth"

pytest: start-infra
	uv run --package supabase_auth pytest --cov=./ --cov-report=xml --cov-report=html -vv

pyrefly:
	uv run --package supabase_auth pyrefly check
help::
	@echo "  pyrefly        -- run pyrefly on supabase_auth"

include ../../infra.mk

AUTH_EXCLUDED_SERVICES := studio,postgrest,realtime,storage-api,imgproxy,edge-runtime,logflare,vector,supavisor,postgres-meta

.DELETE_ON_ERROR:

SIGNING_KEYS := infra/supabase/signing_keys.json

$(SIGNING_KEYS):
	echo '[]' > $@
	supabase --workdir infra gen signing-key --algorithm ES256 --append

start-infra: $(SIGNING_KEYS)
	@$(call retry_start_infra,$(call supabase_cleanup,auth-py-tests),supabase --workdir infra start -x $(AUTH_EXCLUDED_SERVICES))
help::
	@echo "  start-infra    -- start containers for tests"

stop-infra:
	supabase --workdir infra stop
help::
	@echo "  stop-infra     -- stop containers for tests"

build-sync:
	uv run --package supabase_auth scripts/run-unasync.py
help::
	@echo "  build-sync     -- generate _sync from _async code"

clean:
	rm -rf htmlcov .pytest_cache .ruff_cache
	rm -f .coverage coverage.xml
help::
	@echo "  clean          -- clean intermediary files"

build:
	uv build --package supabase_auth
help::
	@echo "  build          -- invoke uv build on supabase_auth package"
