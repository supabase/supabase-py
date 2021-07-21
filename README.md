# supabase-py

[![Documentation Status](https://readthedocs.org/projects/supabase/badge/?version=latest)](https://supabase.readthedocs.io/en/latest/?badge=latest)

Supabase client for Python. This mirrors the design of [supabase-js](https://github.com/supabase/supabase-js/blob/master/README.md)

## Status
- [x] Alpha: We are testing Supabase with a closed set of customers
- [x] Public Alpha: Anyone can sign up over at [app.supabase.io](https://app.supabase.io). But go easy on us, there are a few kinks.
- [ ] Public Beta: Stable enough for most non-enterprise use-cases
- [ ] Public: Production-ready

We are currently in Public Alpha. Watch "releases" of this repo to get notified of major updates.

<kbd><img src="https://gitcdn.link/repo/supabase/supabase/master/web/static/watch-repo.gif" alt="Watch this repo"/></kbd>

## Installation

**Recomended:** First activate your virtual environment, with your favourites system. For example, we like `poetry` and `conda`!

#### PyPi installation

Now install the package.

```bash
pip install supabase-py
```

#### Local installation

You can also installing from after cloning this repo. Install like below to install in Development Mode, which means when you edit the source code the changes will be reflected in your python module.

```bash
pip install -e .
```

## Usage

It's usually best practice to set your api key environment variables in some way that version control doesn't track them, e.g don't put them in your python modules! Set the key and url for the supabase instance in the shell, or better yet, use a dotenv file. Heres how to set the variables in the shell.

```bash
export SUPABASE_URL="my-url-to-my-awesome-supabase-instance"
export SUPABASE_KEY="my-supa-dupa-secret-supabase-api-key"
```

We can then read the keys in the python source code.

```python
import os
from supabase_py import create_client, Client

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

The above test database is a blank supabase instance that has populated the `countries` table with the built in countries script that can be found in the supabase UI. You can launch the test scripts and point to the above test database with the

```bash
SUPABASE_TEST_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlhdCI6MTYxMjYwOTMyMiwiZXhwIjoxOTI4MTg1MzIyfQ.XL9W5I_VRQ4iyQHVQmjG0BkwRfx6eVyYB3uAKcesukg" \
SUPABASE_TEST_URL="https://tfsatoopsijgjhrqplra.supabase.co" \
pytest -x
```

### See issues for what to work on

Rough roadmap:

- [ ] Wrap [Postgrest-py](https://github.com/supabase/postgrest-py/)
- [ ] Wrap [Realtime-py](https://github.com/supabase/realtime-py)
- [x] Wrap [Gotrue-py](https://github.com/J0/gotrue-py)

### Client Library

This is a sample of how you'd use supabase-py. Functions and tests are WIP

## Authenticate

```python
from supabase_py import create_client, Client

url: str = os.environ.get("SUPABASE_TEST_URL")
key: str = os.environ.get("SUPABASE_TEST_KEY")
supabase: Client = create_client(url, key)
# Create a random user login email and password.
random_email: str = "3hf82fijf92@supamail.com"
random_password: str = "fqj13bnf2hiu23h"
user = supabase.auth.sign_up(email=random_email, password=random_password)
```

## Sign-in

```python
from supabase_py import create_client, Client

url: str = os.environ.get("SUPABASE_TEST_URL")
key: str = os.environ.get("SUPABASE_TEST_KEY")
supabase: Client = create_client(url, key)
# Sign in using the user email and password.
random_email: str = "3hf82fijf92@supamail.com"
random_password: str = "fqj13bnf2hiu23h"
user = supabase.auth.sign_in(email=random_email, password=random_password)
```

## Managing Data

#### Insertion of Data
```python
from supabase_py import create_client, Client

url: str = os.environ.get("SUPABASE_TEST_URL")
key: str = os.environ.get("SUPABASE_TEST_KEY")
supabase: Client = create_client(url, key)
data = supabase.table("countries").select("*").execute()
assert len(data.get("data", [])) > 0
```

#### Selection of Data
```python
from supabase_py import create_client, Client

url: str = os.environ.get("SUPABASE_TEST_URL")
key: str = os.environ.get("SUPABASE_TEST_KEY")
supabase: Client = create_client(url, key)
data = supabase.table("countries").select("*").execute()
# Assert we pulled real data.
assert len(data.get("data", [])) > 0
```

## Realtime Changes

```python
subscription = supabase
  .table('countries')
  .on('*',  lambda x: print(x))
  .subscribe()
```

See [Supabase Docs](https://supabase.io/docs/guides/client-libraries) for full list of examples
