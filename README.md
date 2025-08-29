# `supabase-py`

[![CI](https://github.com/supabase/supabase-py/actions/workflows/ci.yml/badge.svg)](https://github.com/supabase/supabase-py/actions/workflows/ci.yml)
[![Version](https://img.shields.io/pypi/v/supabase?color=%2334D058)](https://pypi.org/project/supabase)
[![Coverage Status](https://coveralls.io/repos/github/supabase/supabase-py/badge.svg?branch=main)](https://coveralls.io/repos/github/supabase/supabase-py/badge.svg?branch=main)

Python monorepo for all [Supabase](https://supabase.com) libraries.

- [supabase](src/supabase/README.md)
- [realtime-py](src/realtime/README.md)
- [supabase_functions](src/functions/README.md)
- [storage3](src/storage/README.md)
- [postgrest](src/postgrest/README.md)
- [supabase_auth](src/auth/README.md)

Relevant links:

- Documentation: [supabase.com/docs](https://supabase.com/docs/reference/python/introduction)
- Usage:
  - [GitHub OAuth in your Python Flask app](https://supabase.com/blog/oauth2-login-python-flask-apps)
  - [Python data loading with Supabase](https://supabase.com/blog/loading-data-supabase-python)

## Local Development

### Clone the Repository

```bash
git clone https://github.com/supabase/supabase-py.git
cd supabase-py
```

### Dependencies

This repository relies on the following dependencies for development: 
- `uv` for python project management.
- `make` for command running.
- `docker` for both `postgrest` and `auth` test containers.
- `supabase-cli` for both `storage` and `realtime` test containers.

All of these dependencies are included in the nix shell environment, through `flake.nix`. If you've got `nix` installed, you may prefer to use it through `nix develop`.

### Use a Virtual Environment

We recommend using a virtual environment, preferrably through `uv`, given it is currently the only tool that understands the workspace setup (you can read more about it in [the uv docs](https://docs.astral.sh/uv/concepts/projects/workspaces/)).

```
uv venv supabase-py
source supabase-py/bin/activate
uv sync
```

If you're using nix, the generated `python` executable should have the correct dependencies installed for the whole workspace, given it is derived from the root's `pyproject.toml` using [uv2nix](https://github.com/pyproject-nix/uv2nix).

### Running tests and other commands

We use `make` to store and run the relevant commands. The structure is setup such that each sub package can individually set its command in its own `Makefile`, and the job of the main `Makefile` is just coordinate calling each of them.

For instance, in order to run all tests of all packages, you should use the following root command
```bash
make ci
```
Which internally dispatches `make -C src/{package} tests` calls to each package in the monorepo.

You should also consider using
```bash
make ci -jN # where N is the number of max concurrent jobs, or just -j for infinite jobs
```
To run each of the packages' tests in parallel. This should be generally faster than running in 1 job, but has the downside of messing up the CLI output, so parsing error messages might not be easy.

Other relevant commands include
```bash
make pre-commit # run lints and formmating before commiting
make stop-infra # stops all running containers from all packages
make clean      # delete all intermediary files created by testing
```
All the sub packages command are available from the main root by prefixing the command with `{package_name}.`. Examples:
```bash
make realtime.tests # run only realtime tests
make storage.clean # delete temporary files only in the storage package
```
