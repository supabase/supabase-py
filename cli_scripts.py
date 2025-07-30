from subprocess import Popen


def run_cmd(cmd: str) -> Popen:
    return Popen(cmd.split())


def run_tests():
    # Install requirements
    with (
        run_cmd("uv run pre-commit run --all-files") as precommit,
        run_cmd(
            "uv run pytest --cov=./ --cov-report=xml --cov-report=html -vv"
        ) as pytests,
    ):
        pass
    return precommit.returncode and pytests.returncode
