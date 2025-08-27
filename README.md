# `supabase-py`

Python monorepo for all [Supabase](https://supabase.com) libraries. This is a work in progress, and currently these are the ones contained in this repository:

- [supabase](src/supabase/README.md)
- [realtime](src/realtime/README.md)
- [supabase_functions](src/functions/README.md)
- [storage3](src/storage/README.md)
- [supabase_auth](src/auth/README.md)

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

We recommend activating your virtual environment. For example, we like `uv`, `conda` and `nix`! Click [here](https://docs.python.org/3/library/venv.html) for more about Python virtual environments and working with [conda](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#activating-an-environment) and [uv](https://docs.astral.sh/uv/getting-started/features/). For nix, just install it with flakes enabled.

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

Using nix:
```bash
nix develop
```

### Local installation

You can also install locally after cloning this repo. Install Development mode with `pip install -e`, which makes it editable, so when you edit the source code the changes will be reflected in your python module.

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
