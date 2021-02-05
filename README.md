# supabase-py

[![Documentation Status](https://readthedocs.org/projects/gotrue-py/badge/?version=latest)](https://gotrue-py.readthedocs.io/en/latest/?badge=latest)

Supabase client for Python. This mirrors the design of [supabase-js](https://github.com/supabase/supabase-js/blob/master/README.md)

## Installation

**Recomended:** First activate your virtual environment, with your favourites system. For example, we like `poetry` and `conda`!

#### PyPi installation
Now install the package.
```bash
pip install supabase
```

#### Local installation
You can also installing from after cloning this repo. Install like below to install in Development Mode, which means when you edit the source code the changes will be reflected in your python module.
```bash 
pip install -e .
```
## Usage
```
import supabase_py
supabase_url=""
supabase_key=""
supabase = supabase_py.Client(supabase_url, supabase_key)
```

### Run tests
`python -m pytest`

### See issues for what to work on

Rough roadmap:
- [ ] Wrap [Postgrest-py](https://github.com/supabase/postgrest-py/)
- [ ] Wrap [Realtime-py](https://github.com/supabase/realtime-py)
- [x] Wrap [Gotrue-py](https://github.com/J0/gotrue-py)



### Client Library

This is a sample of how you'd use [supabase-py]. Functions and tests are WIP


## Authenticate 
```
supabase.auth.signUp({
  "email": 'example@email.com',
  "password": 'example-password',
})
```


## Sign-in
```
supabase.auth.signIn({
  "email": 'example@email.com',
  "password": 'example-password',
})
```


## Sign-in(Auth provider). This is not supported yet
```
supabase.auth.signIn({
  // provider can be 'github', 'google', 'gitlab', or 'bitbucket'
  "provider": 'github'
})
```


## Managing Data
```
supabase
  .from('countries')
  .select("
    name,
    cities (
      name
    )
  ")
```

## Realtime Changes
```
mySubscription = supabase
  .from('countries')
  .on('*',  lambda x: print(x))
  .subscribe()
  ```
See [Supabase Docs](https://supabase.io/docs/guides/client-libraries) for full list of examples
