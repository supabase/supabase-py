## v1.0.0 (2022-01-02)

### Fix

- set correct main branch in ci.yml
- set correct main branch in ci.yml
- set correct main branch in ci.yml
- update gotrue version and modify client options class
- update gotrue version and modify client options class
- remove setup.py
- ci.yml max parallel config
- github action max parallel in one
- export envs and fix tests
- error in Makefile
- remove deadweight test
- ensure python37 compat
- default value for `name` in create_bucket

### Refactor

- realtime_py -> realtime

### Feat

- use directly sync postgrest client and remove unused code
- use directly sync postgrest client and remove unused code
- unify http client to be httpx
- unify http client to be httpx
- add header to query builder
- upload files include mime type
- add mime type to uploaded files
- create custom StorageException

## v0.0.3 (2021-10-13)

### Feat

- add async support to storage buckets API
- add docs for query_builder and storage_bucket
- add upload
- add download function
- Add more functions to storage file api
- add create_signed_url

### Fix

- missing json bodies in patch and put requests
- missing json bodies in patch and put requests
- get create_signed_url working
- resolve merge conflicts
- resolve merge conflicts

### Refactor

- update test client to use fixture
- update test client

## v0.0.2 (2021-04-05)
