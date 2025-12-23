help::
	@echo "Available commands"
	@echo "  help           -- (default) print this message"

tests: mypy pytest
help::
	@echo "  tests          -- run all tests for supabase_functions package"

pytest:
	uv run --package supabase_functions pytest --cov=./ --cov-report=xml --cov-report=html -vv
help::
	@echo "  pytest         -- run pytest on supabase_functions package"

mypy:
	uv run --package supabase_functions mypy src/supabase_functions tests
help::
	@echo "  mypy           -- run mypy on supabase_functions package"

clean:
	rm -rf htmlcov .pytest_cache .mypy_cache .ruff_cache
	rm -f .coverage coverage.xml
help::
	@echo "  clean          -- clean intermediary files"

build:
	uv build --package supabase_functions
help::
	@echo "  build          -- invoke uv build on supabase_functions package"
