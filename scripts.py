import subprocess


class Command:
    @staticmethod
    def run(cmd):
        return subprocess.run(cmd, shell=True, check=True)


def install():
    return Command.run("poetry install --verbose")


def lint():
    return Command.run("poetry run pre-commit run --all-files")


def coverage():
    return Command.run("poetry run pytest --cov=./ --cov-report=html -vv")
