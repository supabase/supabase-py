install:
	poetry install

install_poetry:
	curl -sSL https://install.python-poetry.org | python -
	poetry install

tests_pre_commit:
	poetry run pre-commit run --all-files

tests_only:
	poetry run pytest --cov=./ --cov-report=xml --cov-report=html -vv

tests: install tests_only tests_pre_commit

run_tests: tests