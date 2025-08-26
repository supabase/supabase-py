tests: pytest

pytest: run_infra
	uv run --package supabase_auth pytest --cov=./ --cov-report=xml --cov-report=html -vv

run_infra:
	cd infra &&\
	docker compose down &&\
	docker compose up -d

clean_infra:
	cd infra &&\
	docker compose down --remove-orphans &&\
	docker system prune -a --volumes -f

stop_infra:
	cd infra &&\
	docker compose down --remove-orphans

sync_infra:
	uv run --package supabase_auth scripts/gh-download.py --repo=supabase/gotrue-js --branch=master --folder=infra

build_sync:
	poetry run unasync supabase_auth tests
