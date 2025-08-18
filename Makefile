.PHONY: ci, default, pre-commit

default:
	@echo "Available targets are: ci, pre-commit"

ci: pre-commit
	make -C src/realtime tests
	make -C src/supabase tests

publish:
	uv build --project realtime
	uv build --project supabase
	uv publish

pre-commit:
	uv run pre-commit run --all-files
