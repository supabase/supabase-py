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
	mypy src/supabase_functions
	mypy tests
help::
	@echo "  mypy           -- run mypy on supabase_functions package"

unasync:
	uv run --package supabase_functions run-unasync.py
help::
	@echo "  unasync        -- invoke run-unasync.py helper"

build-sync: unasync
	sed -i '0,/SyncMock, /{s/SyncMock, //}' tests/_sync/test_function_client.py
	sed -i 's/SyncMock/Mock/g' tests/_sync/test_function_client.py
	sed -i 's/SyncClient/Client/g' src/supabase_functions/_sync/functions_client.py tests/_sync/test_function_client.py
help::
	@echo "  build-sync     -- invoke run-unasync.py helper"

clean:
	rm -rf htmlcov .pytest_cache .mypy_cache .ruff_cache
	rm -f .coverage coverage.xml
help::
	@echo "  clean          -- clean intermediary files"

build:
	uv build --package supabase_functions
help::
	@echo "  build          -- invoke uv build on supabase_functions package"
