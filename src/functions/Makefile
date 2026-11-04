help::
	@echo "Available commands"
	@echo "  help           -- (default) print this message"

tests: pyrefly pytest
help::
	@echo "  tests          -- run all tests for supabase_functions package"

pytest:
	uv run --package supabase_functions pytest --cov=./ --cov-report=xml --cov-report=html -vv
help::
	@echo "  pytest         -- run pytest on supabase_functions package"

pyrefly:
	uv run --package supabase_functions pyrefly check
help::
	@echo "  pyrefly        -- run pyrefly on supabase_functions"

clean:
	rm -rf htmlcov .pytest_cache .ruff_cache
	rm -f .coverage coverage.xml
help::
	@echo "  clean          -- clean intermediary files"

build:
	uv build --package supabase_functions
help::
	@echo "  build          -- invoke uv build on supabase_functions package"
