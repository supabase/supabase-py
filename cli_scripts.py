import subprocess


def uvx(*cmds: str):
    return subprocess.run(["uv", "run", *cmds], check=True)


def precommit():
    return uvx("pre-commit", "run", "--all-files")


def pytest():
    return uvx("pytest", "--cov=./", "--cov-report=xml", "--cov-report=html", "-vv")


def unasync():
    return uvx("unasync", "supabase", "tests")


def sed(before: str, after: str):
    return subprocess.run(["sed", "-i", "", before, after], check=True)

def build_sync():
    substs = [
        ('s/asyncio.create_task(self.realtime.set_auth(access_token))//g', "supabase/_sync/client.py"),
        ('s/asynch/synch/g', "supabase/_sync/auth_client.py"),
        ('s/Async/Sync/g', "supabase/_sync/auth_client.py"),
        ('s/Async/Sync/g', "supabase/_sync/client.py"),
        ('s/create_async_client/create_client/g', "tests/_sync/test_client.py"),
        ('s/SyncClient/Client/gi', "tests/_sync/test_client.py"),
        ('s/SyncHTTPTransport/HTTPTransport/g', "tests/_sync/test_client.py"),
        ('s/SyncMock/Mock/g', "tests/_sync/test_client.py"),
    ]
    unasync()
    for (left, right) in substs:
        sed(left, right)

def run_tests():
    precommit()
    pytest()
