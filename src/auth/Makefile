tests: pytest

pytest: run-infra
	uv run --exact --package supabase_auth pytest --cov=./ --cov-report=xml --cov-report=html -vv

run-infra:
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
	uv run --exact --package supabase_auth scripts/gh-download.py --repo=supabase/gotrue-js --branch=master --folder=infra

build-sync:
	uv run --exact --package supabase_auth scripts/run-unasync.py
