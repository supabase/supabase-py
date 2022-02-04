powershell -Command {
    poetry install;
    poetry run pytest --cov=./ --cov-report=xml --cov-report=html -vv;
    poetry run pre-commit run --all-files;
}
