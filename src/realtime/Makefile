.PHONY: pytest mypy tests infra stop-infra

mypy:
	uv run --package realtime mypy src/realtime

start-infra:
	supabase start --workdir infra -x studio,mailpit,edge-runtime,logflare,vector,supavisor,imgproxy,storage-api

stop-infra:
	supabase --workdir infra stop

tests: mypy pytest

pytest: start-infra
	uv run --package realtime pytest --cov=realtime --cov-report=xml --cov-report=html -vv

clean:
	rm -rf htmlcov .pytest_cache .mypy_cache .ruff_cache
	rm -f .coverage coverage.xml

build:
	uv build --package realtime
