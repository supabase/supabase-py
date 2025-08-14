.PHONY: pytest pre-commit mypy tests infra stop-infra

mypy:
	uv run --exact --package realtime mypy src/realtime

infra:
	supabase start --workdir infra -x studio,mailpit,edge-runtime,logflare,vector,supavisor,imgproxy,storage-api

stop-infra:
	supabase --workdir infra stop

tests: mypy infra pytest

pytest:
	uv run --exact --package realtime pytest --cov=realtime --cov-report=xml --cov-report=html -vv
