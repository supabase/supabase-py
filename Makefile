.PHONY: ci

pre-commit:
	uv run pre-commit run --all-files

ci: pre-commit
	cd src/realtime && make tests
	cd src/supabase && make tests
