# `supabase-py`

Python monorepo for all [Supabase](https://supabase.com) libraries.

- [supabase](src/supabase/README.md)
- [realtime](src/realtime/README.md)

Relevant links:

- Documentation: [supabase.com/docs](https://supabase.com/docs/reference/python/introduction)
- Usage:
  - [GitHub OAuth in your Python Flask app](https://supabase.com/blog/oauth2-login-python-flask-apps)
  - [Python data loading with Supabase](https://supabase.com/blog/loading-data-supabase-python)

## Set up a Local Development Environment

### Clone the Repository

```bash
git clone https://github.com/supabase/supabase-py.git
cd supabase-py
```

### Create and Activate a Virtual Environment

We recommend activating your virtual environment. For example, we like `uv` and `conda`! Click [here](https://docs.python.org/3/library/venv.html) for more about Python virtual environments and working with [conda](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#activating-an-environment) and [uv](https://docs.astral.sh/uv/getting-started/features/).

Using uv:
```
uv venv supabase-py
source supabase-py/bin/activate
uv sync
```

Using venv (Python 3 built-in):

```bash
python3 -m venv env
source env/bin/activate  # On Windows, use .\env\Scripts\activate
```

Using conda:

```bash
conda create --name supabase-py
conda activate supabase-py
```

### Local installation

You can also install locally after cloning this repo. Install Development mode with `pip install -e`, which makes it editable, so when you edit the source code the changes will be reflected in your python module.

## Roadmap

- [x] Wrap [Postgrest-py](https://github.com/supabase/postgrest-py/)
  - [x] Add remaining filters
  - [x] Add support for EXPLAIN
  - [ ] Add proper error handling
  - [x] Use `sanitize_param()` to sanitize inputs.
  - [x] Fix client-side timeouts for long running queries.
  - [x] Enable HTTP2 by default.
  - [x] Enable follow redirects by default.
  - [x] Enable keep-alive by default.
  - [x] Enable running with unverified SSL via `verify=False`.
  - [x] Add Stalebot.
  - [x] Update CI (linters, etc).
  - [x] Check cyclomatic complexity and fix if needed (mccabe, prospector).

- [ ] Wrap [Realtime-py](https://github.com/supabase/realtime-py)
  - [ ] Integrate with Supabase-py
  - [ ] Support WALRUS
  - [ ] Support broadcast (to check if already supported)
  - [x] Add `close()` method to close a socket.
  - [x] Add Stalebot.
  - [x] Update CI (linters, etc).
  - [x] Check cyclomatic complexity and fix if needed (mccabe, prospector).

- [x] Wrap [auth-py](https://github.com/supabase/auth-py)
  - [x] Remove references to GoTrue-js v1 and do a proper release
  - [ ] Test and document common flows (e.g. sign in with OAuth, sign in with OTP)
  - [ ] Add MFA methods
  - [x] Add SSO methods
  - [x] Add Proof Key for Code Exchange (PKCE) methods. Unlike the JS library, we do not currently plan to support Magic Link (PKCE). Please use the [token hash](https://supabase.com/docs/guides/auth/server-side/email-based-auth-with-pkce-flow-for-ssr#create-api-endpoint-for-handling-tokenhash) in tandem with `verifyOTP` instead.
  - [x] Add `is_anonymous` boolean property.
  - [x] Add `sign_in_with_id_token()` method.
  - [x] Add `sign_in_with_sso()` method.
  - [x] Enable HTTP2 by default.
  - [x] Enable follow redirects by default.
  - [x] Enable keep-alive by default.
  - [x] Enable running with unverified SSL via `verify=False`.
  - [x] Add Stalebot.
  - [x] Update CI (linters, etc).
  - [x] Check cyclomatic complexity and fix if needed (mccabe, prospector).

- [x] Wrap [storage-py](https://github.com/supabase/storage-py)
  - [ ] Support resumable uploads
  - [x] Setup testing environment
  - [x] Fix client-side timeouts for long running operations.
  - [x] Enable HTTP2 by default.
  - [x] Enable follow redirects by default.
  - [x] Enable keep-alive by default.
  - [x] Enable running with unverified SSL via `verify=False`.
  - [x] Add Stalebot.
  - [x] Update CI (linters, etc).
  - [x] Check cyclomatic complexity and fix if needed (mccabe, prospector).
  - [x] Document how to properly upload different file types (e.g. jpeg/png and download it)

- [x] Wrap [functions-py](https://github.com/supabase/functions-py)
  - [x] Fix client-side timeouts for long running functions.
  - [x] Enable HTTP2 by default.
  - [x] Enable follow redirects by default.
  - [x] Enable keep-alive by default.
  - [x] Enable running with unverified SSL via `verify=False`.
  - [x] Add Regions support.
  - [x] Add Stalebot.
  - [x] Update CI (linters, etc).
  - [x] Check cyclomatic complexity and fix if needed (mccabe, prospector).


### Overall Tasks

- [x] Add async support across the entire library
- [ ] Add FastAPI helper library (external to supabase-py)
- [ ] Add `django-supabase-postgrest` (external to supabase-py)

## Contributing

Contributing to the Python libraries are a great way to get involved with the Supabase community. Reach out to us on [Discord](https://discord.supabase.com) or on our [Github Discussions](https://github.com/orgs/supabase/discussions) page if you want to get involved.

### Running Tests

Currently, the test suites are in a state of flux. We are expanding our clients' tests to ensure things are working, and for now can connect to this test instance, which is populated with the following table:

<p align="center">
  <img width="720" height="481" src="https://i.ibb.co/Bq7Kdty/db.png">
</p>

The above test database is a blank supabase instance that has populated the `countries` table with the built-in countries script that can be found in the supabase UI. You can launch the test scripts and point to the above test database by running

```bash
./test.sh
```

## Badges

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?label=license)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/supabase/supabase-py/actions/workflows/ci.yml/badge.svg)](https://github.com/supabase/supabase-py/actions/workflows/ci.yml)
[![Python](https://img.shields.io/pypi/pyversions/supabase)](https://pypi.org/project/supabase)
[![Version](https://img.shields.io/pypi/v/supabase?color=%2334D058)](https://pypi.org/project/supabase)
[![Codecov](https://codecov.io/gh/supabase/supabase-py/branch/develop/graph/badge.svg)](https://codecov.io/gh/supabase/supabase-py)
[![Last commit](https://img.shields.io/github/last-commit/supabase/supabase-py.svg?style=flat)](https://github.com/supabase/supabase-py/commits)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/m/supabase/supabase-py)](https://github.com/supabase/supabase-py/commits)
[![Github Stars](https://img.shields.io/github/stars/supabase/supabase-py?style=flat&logo=github)](https://github.com/supabase/supabase-py/stargazers)
[![Github Forks](https://img.shields.io/github/forks/supabase/supabase-py?style=flat&logo=github)](https://github.com/supabase/supabase-py/network/members)
[![Github Watchers](https://img.shields.io/github/watchers/supabase/supabase-py?style=flat&logo=github)](https://github.com/supabase/supabase-py)
[![GitHub contributors](https://img.shields.io/github/contributors/supabase/supabase-py)](https://github.com/supabase/supabase-py/graphs/contributors)
