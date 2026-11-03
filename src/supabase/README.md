# `supabase-py`

Python client for [Supabase](https://supabase.com)

- Documentation: [supabase.com/docs](https://supabase.com/docs/reference/python/introduction)
- Usage:
  - [GitHub OAuth in your Python Flask app](https://supabase.com/blog/oauth2-login-python-flask-apps)
  - [Python data loading with Supabase](https://supabase.com/blog/loading-data-supabase-python)

### PyPI installation

Install the package (for Python >= 3.9):

```bash
# with pip
pip install supabase

# with uv
uv add supabase

# with conda
conda install -c conda-forge supabase
```

## Usage

Set your Supabase environment variables in a dotenv file, or using the shell:

```bash
export SUPABASE_URL="my-url-to-my-awesome-supabase-instance"
export SUPABASE_KEY="my-supa-dupa-secret-supabase-api-key"
```

Init client:

```python
import os
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)
```

Use the supabase client to interface with your database.

### Sign-up

```python
user = supabase.auth.sign_up({ "email": users_email, "password": users_password })
```

### Sign-in

```python
user = supabase.auth.sign_in_with_password({ "email": users_email, "password": users_password })
```

### Insert Data

```python
data = supabase.table("countries").insert({"name":"Germany"}).execute()

# Assert we pulled real data.
assert len(data.data) > 0
```

### Select Data

```python
data = supabase.table("countries").select("*").eq("country", "IL").execute()

# Assert we pulled real data.
assert len(data.data) > 0
```

### Update Data

```python
data = supabase.table("countries").update({"country": "Indonesia", "capital_city": "Jakarta"}).eq("id", 1).execute()
```

### Update data with duplicate keys

```python
country = {
  "country": "United Kingdom",
  "capital_city": "London" # This was missing when it was added
}

data = supabase.table("countries").upsert(country).execute()
assert len(data.data) > 0
```

### Delete Data

```python
data = supabase.table("countries").delete().eq("id", 1).execute()
```

### Call Edge Functions

```python
def test_func():
  try:
    resp = supabase.functions.invoke("hello-world", invoke_options={'body':{}})
    return resp
  except (FunctionsRelayError, FunctionsHttpError) as exception:
    err = exception.to_dict()
    print(err.get("message"))
```

### Download a file from Storage

```python
bucket_name: str = "photos"

data = supabase.storage.from_(bucket_name).download("photo1.png")
```

### Upload a file

```python
bucket_name: str = "photos"
new_file = getUserFile()

data = supabase.storage.from_(bucket_name).upload("/user1/profile.png", new_file)
```

### Remove a file

```python
bucket_name: str = "photos"

data = supabase.storage.from_(bucket_name).remove(["old_photo.png", "image5.jpg"])
```

### List all files

```python
bucket_name: str = "charts"

data = supabase.storage.from_(bucket_name).list()
```

### Move and rename files

```python
bucket_name: str = "charts"
old_file_path: str = "generic/graph1.png"
new_file_path: str = "important/revenue.png"

data = supabase.storage.from_(bucket_name).move(old_file_path, new_file_path)
```

## Important: Proper Client Shutdown

To ensure the Supabase client terminates correctly and to prevent resource leaks, you **must** explicitly call:

```python
client.auth.sign_out()
```
