.PHONY: ci, default, pre-commit

default:
	@echo "Available targets are: ci, pre-commit, publish"

ci: pre-commit
	make -C src/realtime tests
	make -C src/functions tests
	make -C src/supabase tests

publish:
	uv build --project realtime
	uv build --project supabase
	uv build --project functions
	uv publish

pre-commit:
	uv run pre-commit run --all-files
