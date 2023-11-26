# supabase-py

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?label=license)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/supabase-community/supabase-py/actions/workflows/ci.yml/badge.svg)](https://github.com/supabase-community/supabase-py/actions/workflows/ci.yml)
[![Python](https://img.shields.io/pypi/pyversions/supabase)](https://pypi.org/project/supabase)
[![Version](https://img.shields.io/pypi/v/supabase?color=%2334D058)](https://pypi.org/project/supabase)
[![Codecov](https://codecov.io/gh/supabase-community/supabase-py/branch/develop/graph/badge.svg)](https://codecov.io/gh/supabase-community/supabase-py)
[![Last commit](https://img.shields.io/github/last-commit/supabase-community/supabase-py.svg?style=flat)](https://github.com/supabase-community/supabase-py/commits)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/m/supabase-community/supabase-py)](https://github.com/supabase-community/supabase-py/commits)
[![Github Stars](https://img.shields.io/github/stars/supabase-community/supabase-py?style=flat&logo=github)](https://github.com/supabase-community/supabase-py/stargazers)
[![Github Forks](https://img.shields.io/github/forks/supabase-community/supabase-py?style=flat&logo=github)](https://github.com/supabase-community/supabase-py/network/members)
[![Github Watchers](https://img.shields.io/github/watchers/supabase-community/supabase-py?style=flat&logo=github)](https://github.com/supabase-community/supabase-py)
[![GitHub contributors](https://img.shields.io/github/contributors/supabase-community/supabase-py)](https://github.com/supabase-community/supabase-py/graphs/contributors)

Supabase client for Python. This mirrors the design of [supabase-js](https://github.com/supabase/supabase-js/blob/master/README.md)

| Status | Stability | Goal |
| ------ | ------ | ---- |
| ✅ | Alpha | We are testing Supabase with a closed set of customers |
| ✅ | Public Alpha | Anyone can sign up over at [app.supabase.io](https://app.supabase.com). But go easy on us, there are a few kinks. |
| 🚧 | Public Beta | Stable enough for most non-enterprise use-cases |
| ❌ | Public | Production-ready |

We are currently in Public Alpha. Watch "releases" of this repo to get notified of major updates.


## Installation

**Recomended:** First activate your virtual environment, with your favourite system. For example, we like `poetry` and `conda`!

### PyPi installation

Now install the package. (for > Python 3.7)

```bash
# with pip
pip install supabase

# with conda
conda install -c conda-forge supabase
```

### Local installation

You can also install locally after cloning this repo. Install Development mode with ``pip install -e``, which makes it so when you edit the source code the changes will be reflected in your python module.

## Usage

It's usually best practice to set your api key environment variables in some way that version control doesn't track them, e.g don't put them in your python modules! Set the key and url for the supabase instance in the shell, or better yet, use a dotenv file. Heres how to set the variables in the shell.

```bash
export SUPABASE_URL="my-url-to-my-awesome-supabase-instance"
export SUPABASE_KEY="my-supa-dupa-secret-supabase-api-key"
```

We can then read the keys in the python source code.

```python
import os
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)
```

Use the supabase client to interface with your database.

### Running Tests

Currently the test suites are in a state of flux. We are expanding our clients tests to ensure things are working, and for now can connect to this test instance, that is populated with the following table:

<p align="center">
  <img width="720" height="481" src="https://i.ibb.co/Bq7Kdty/db.png">
</p>

The above test database is a blank supabase instance that has populated the `countries` table with the built in countries script that can be found in the supabase UI. You can launch the test scripts and point to the above test database by running

```bash
./test.sh
```

### See issues for what to work on

Rough roadmap:

- [x] Wrap [Postgrest-py](https://github.com/supabase-community/postgrest-py/)
  - [ ] Add remaining filters
  - [ ] Add support for EXPLAIN
  - [ ] Add proper error handling
- [ ] Wrap [Realtime-py](https://github.com/supabase-community/realtime-py)
    - [ ]  Integrate with Supabase-py
    - [ ]  Support WALRUS
    - [ ]  Support broadcast (to check if already supported)
- [x] Wrap [Gotrue-py](https://github.com/supabase-community/gotrue-py)
    - [ ] Remove references to GoTrue-js v1 and do a proper release
    - [ ] Test and document common flows (e.g. sign in with OAuth, sign in with OTP)
    - [ ] Add MFA methods and SSO methods
    - [ ] Add Proof Key for Code Exchange (PKCE) methods
- [x] Wrap [storage-py](https://github.com/supabase-community/storage-py)
    - [ ]  Support resumable uploads
    - [ ]  Setup testing environment
    - [ ]  Document how to properly upload different file types (e.g. jpeg/png and download it)
- [x] Wrap [functions-py](https://github.com/supabase-community/functions-py)

Overall Tasks:
- [ ] Add async support across the entire library
- [ ] Add FastAPI helper library (external to supabase-py)
- [ ] Add `django-supabase-postgrest` (external to supabase-py)

### Client Library

## Authenticate

```python
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_TEST_URL")
key: str = os.environ.get("SUPABASE_TEST_KEY")
supabase: Client = create_client(url, key)
# Create a random user login email and password.
random_email: str = "3hf82fijf92@supamail.com"
random_password: str = "fqj13bnf2hiu23h"
user = supabase.auth.sign_up({ "email": random_email, "password": random_password })
```

## Sign-in

```python
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_TEST_URL")
key: str = os.environ.get("SUPABASE_TEST_KEY")
supabase: Client = create_client(url, key)
# Sign in using the user email and password.
random_email: str = "3hf82fijf92@supamail.com"
random_password: str = "fqj13bnf2hiu23h"
user = supabase.auth.sign_in_with_password({ "email": random_email, "password": random_password })
```

## Managing Data

### Insertion of Data

```python
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_TEST_URL")
key: str = os.environ.get("SUPABASE_TEST_KEY")
supabase: Client = create_client(url, key)
data = supabase.table("countries").insert({"name":"Germany"}).execute()
assert len(data.data) > 0
```

### Selection of Data

```python
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_TEST_URL")
key: str = os.environ.get("SUPABASE_TEST_KEY")
supabase: Client = create_client(url, key)
data = supabase.table("countries").select("*").eq("country", "IL").execute()
# Assert we pulled real data.
assert len(data.data) > 0
```

### Update of Data

```python
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_TEST_URL")
key: str = os.environ.get("SUPABASE_TEST_KEY")
supabase: Client = create_client(url, key)
data = supabase.table("countries").update({"country": "Indonesia", "capital_city": "Jakarta"}).eq("id", 1).execute()
```

### Update data of duplicate keys

```python
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_TEST_URL")
key: str = os.environ.get("SUPABASE_TEST_KEY")
supabase: Client = create_client(url, key)

country = {
  "country": "United Kingdom",
  "capital_city": "London" # this was missing when it was added
}

data = supabase.table("countries").upsert(country).execute()
assert len(data.data) > 0
```

### Deletion of Data

```python
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_TEST_URL")
key: str = os.environ.get("SUPABASE_TEST_KEY")
supabase: Client = create_client(url, key)
data = supabase.table("countries").delete().eq("id", 1).execute()
```

### Supabase Functions

```python
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_TEST_URL")
key: str = os.environ.get("SUPABASE_TEST_KEY")
supabase: Client = create_client(url, key)

def test_func():
  try:
    resp = supabase.functions.invoke("hello-world", invoke_options={'body':{}})
    return resp
  except (FunctionsRelayError, FunctionsHttpError) as exception:
    err = exception.to_dict()
    print(err.get("message"))
```

## Storage

### Download a file

```python
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_TEST_URL")
key: str = os.environ.get("SUPABASE_TEST_KEY")
supabase: Client = create_client(url, key)

bucket_name: str = "photos"

data = supabase.storage.from_(bucket_name).download("photo1.png")
```

### Upload a file

```python
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_TEST_URL")
key: str = os.environ.get("SUPABASE_TEST_KEY")
supabase: Client = create_client(url, key)

bucket_name: str = "photos"
new_file = getUserFile()

data = supabase.storage.from_(bucket_name).upload("/user1/profile.png", new_file)
```

### Remove a file

```python
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_TEST_URL")
key: str = os.environ.get("SUPABASE_TEST_KEY")
supabase: Client = create_client(url, key)

bucket_name: str = "photos"

data = supabase.storage.from_(bucket_name).remove(["old_photo.png", "image5.jpg"])
```

### List all files

```python
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_TEST_URL")
key: str = os.environ.get("SUPABASE_TEST_KEY")
supabase: Client = create_client(url, key)

bucket_name: str = "charts"

data = supabase.storage.from_(bucket_name).list()
```

### Move and rename file

```python
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_TEST_URL")
key: str = os.environ.get("SUPABASE_TEST_KEY")
supabase: Client = create_client(url, key)

bucket_name: str = "charts"
old_file_path: str = "generic/graph1.png"
new_file_path: str = "important/revenue.png"

data = supabase.storage.from_(bucket_name).move(old_file_path, new_file_path)
```


## Realtime Changes

Realtime changes are unfortunately still a WIP. Feel free to file PRs to [realtime-py](https://github.com/supabase-community/realtime-py)

See [Supabase Docs](https://supabase.com/docs/guides/client-libraries) for full list of examples

## Python and Supabase Resources

- [Python data loading with Supabase](https://supabase.com/blog/loading-data-supabase-python)
- [Visualizing Supabase Data using Metabase](https://supabase.com/blog/visualizing-supabase-data-using-metabase)
