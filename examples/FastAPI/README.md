### 🐴 Why
This tutorial should serve as an example of using supabase api to connect to your database instance and build a service to periodically cache and serve consumer credit data on client request. This project covers redis as a caching mechanism, supabase to support our postgres instance, and fastapi for our framework, all deployed on Deta Cloud.

See docs for more information,

### ☂️ Setting up your environment

Setup your virtual environment:

```bash
python3 -m venv env
```

Activating your environment

```zsh
source env/bin/activate
```

In the root directory run the following:

```bash
pip install -r requirements.txt
```

After setting up supabase you need to create a `.env` file with the following:

```bash
URL=<Supabase Project URL>
KEY=<Supabase Project Key>
LOCAL_REDIS_INSTANCE=redis://127.0.0.1:6379
```

### 🤖 Starting Redis in development environment

To begin working with redis, run the following command, after completion open a new terminal window.

```zsh
redis-server
```

### 👾 Activating your development server

To start your local server run the following command

```zsh
uvicorn main:app --reload
```

On success of the commad you should see;

```zsh
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [13385] using watchgod
INFO:     Started server process [13387]
2022-02-11 19:32:12,509:INFO - Started server process [13387]
INFO:     Waiting for application startup.
2022-02-11 19:32:12,509:INFO - Waiting for application startup.
2022-02-11 19:32:12,510:INFO -  02/11/2022 07:32:12 PM | CONNECT_BEGIN: Attempting to connect to Redis server...
2022-02-11 19:32:12,511:INFO -  02/11/2022 07:32:12 PM | CONNECT_SUCCESS: Redis client is connected to server.
INFO:     Application startup complete.
2022-02-11 19:32:12,511:INFO - Application startup complete.
```

### 🎾 Endpoints

Introduction to your application.
```bash
http "http://127.0.0.1:8000/"

HTTP/1.1 200 OK
content-length: 102
content-type: application/json
date: Wed, 16 Feb 2022 22:01:14 GMT
server: uvicorn

{
    "👋 Hello": "Please refer to the readme documentation for more or visit http://localhost:8000/docs"
}
```

Working with your redis cache, the following call will pull data
from your supabase database, and cache it.

The x-fastapi-cache header field indicates that this response was found in the Redis cache (a.k.a. a Hit).

The only other possible value for this field is Miss. The expires field and max-age value in the cache-control field indicate that this response will be considered fresh for 604321 seconds(1 week). This is expected since it was specified in the @cache decorator.

The etag field is an identifier that is created by converting the response data to a string and applying a hash function. If a request containing the if-none-match header is received, any etag value(s) included in the request will be used to determine if the data requested is the same as the data stored in the cache. If they are the same, a 304 NOT MODIFIED response will be sent. If they are not the same, the cached data will be sent with a 200 OK response.

```bash
# Command
http "http://127.0.0.1:8000/cachedResults"

# Response Headers
HTTP/1.1 200 OK
cache-control: max-age=604321
content-length: 894
content-type: application/json
date: Wed, 16 Feb 2022 21:53:56 GMT
etag: W/-9174636245072902018
expires: Wed, 23 Feb 2022 21:45:57 GMT
server: uvicorn
x-supafast-cache: Hit
```


### Docs

- [Installing Redis](https://redis.io/topics/quickstart)
- [Setting up Supabase](https://supabase.com/docs/reference)
- [Getting started with FastApi](https://fastapi.tiangolo.com/tutorial/)
- [Tutorial Author](https://github.com/cloudguruab)
