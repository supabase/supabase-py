from subprocess import Popen


def spawn(cmd: str) -> Popen:
    return Popen(cmd.split())


def spawn_precommit() -> Popen:
    return spawn("uv run pre-commit run --all-files")


def spawn_pytest() -> Popen:
    return spawn("uv run pytest --cov=./ --cov-report=xml --cov-report=html -vv")


def run_tests():
    # Install requirements
    with spawn_precommit() as precommit, spawn_pytest() as pytests:
        pass  # implicitly wait for all of them to return
    return precommit.returncode and pytests.returncode
