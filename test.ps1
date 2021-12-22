powershell -Command {
    $env:SUPABASE_TEST_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlhdCI6MTYzNTAwODQ4NywiZXhwIjoxOTUwNTg0NDg3fQ.l8IgkO7TQokGSc9OJoobXIVXsOXkilXl4Ak6SCX5qI8";
    $env:SUPABASE_TEST_URL = "https://ibrydvrsxoapzgtnhpso.supabase.co";
    poetry install;
    poetry run pytest --cov=./ --cov-report=xml --cov-report=html -vv;
    poetry run pre-commit run --all-files;
}
