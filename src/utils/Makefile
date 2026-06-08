help::
	@echo "Available commands"
	@echo "  help           -- (default) print this message"

tests: mypy
help::
	@echo "  tests          -- run all tests for supabase_utils package"

mypy:
	uv run --package supabase_utils mypy src/supabase_utils
help::
	@echo "  mypy           -- run mypy on supabase_utils package"

clean:
	rm -rf htmlcov .pytest_cache .mypy_cache .ruff_cache
	rm -f .coverage coverage.xml
help::
	@echo "  clean          -- clean intermediary files"

build:
	uv build --package supabase_utils
help::
	@echo "  build          -- invoke uv build on supabase_utils package"
