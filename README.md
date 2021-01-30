# supabase-py

[![Documentation Status](https://readthedocs.org/projects/gotrue-py/badge/?version=latest)](https://gotrue-py.readthedocs.io/en/latest/?badge=latest)

Supabase client for Python. This mirrors the design of [supabase-js](https://github.com/supabase/supabase-js/blob/master/README.md)

## Usage

`pip3 install supabase`


```
import supabase
supabaseUrl=""
supabaseKey=""
client = supabase.Client(supabaseUrl, supabaseKey)
```


### See issues for what to work on

Rough roadmap:
- [ ] Wrap [Postgrest-py](https://github.com/supabase/postgrest-py/)
- [ ] Wrap [Realtime-py](https://github.com/supabase/realtime-py)
- [ ] Wrap [Gotrue-py](https://github.com/J0/gotrue-py)


### Client Library

This is how you'd use [supabase-py]