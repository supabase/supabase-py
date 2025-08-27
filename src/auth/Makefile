tests: pytest

pytest: start-infra
	uv run --package supabase_auth pytest --cov=./ --cov-report=xml --cov-report=html -vv

start-infra:
	cd infra &&\
	docker compose down &&\
	docker compose up -d
	sleep 2

clean-infra:
	cd infra &&\
	docker compose down --remove-orphans &&\
	docker system prune -a --volumes -f

stop-infra:
	cd infra &&\
	docker compose down --remove-orphans

sync-infra:
	uv run --package supabase_auth scripts/gh-download.py --repo=supabase/gotrue-js --branch=master --folder=infra

build-sync:
	uv run --package supabase_auth scripts/run-unasync.py

clean:
	rm -rf htmlcov .pytest_cache .mypy_cache .ruff_cache
	rm -f .coverage coverage.xml

build:
	uv build --package supabase_auth
