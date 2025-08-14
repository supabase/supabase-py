.PHONY: pytest pre-commit mypy tests infra stop-infra

pre-commit:
	uv run pre-commit run --all-files

mypy:
	uv run --exact --package realtime mypy src/realtime

infra:
	supabase start --workdir infra -x studio,mailpit,edge-runtime,logflare,vector,supavisor,imgproxy,storage-api

stop-infra:
	supabase --workdir infra stop

tests: pre-commit mypy infra pytest

pytest:
	uv run --exact --package realtime pytest --cov=realtime --cov-report=xml --cov-report=html -vv
