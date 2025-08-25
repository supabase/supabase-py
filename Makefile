.PHONY: ci, default, pre-commit

default:
	@echo "Available targets are: ci, pre-commit, publish"

ci: pre-commit
	make -C src/functions tests
	make -C src/realtime tests
	make -C src/storage tests
	make -C src/supabase tests

publish:
	uv build --package realtime
	uv build --package storage3
	uv build --package supabase_functions
	uv build --package supabase
	uv publish

pre-commit:
	uv run pre-commit run --all-files
