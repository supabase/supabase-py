import json

# supabase client
from config import Config

# database cursor to supabase
from data.database import SupabaseDB
from fastapi import FastAPI, Request, Response

# redis related imports
from fastapi_redis_cache import FastApiRedisCache, cache_one_week

# application factory
app = FastAPI(title="Supafast Tutorial", debug=True)


@app.on_event("startup")
def onStart():
    """
    Helper function for on event handler in FastAPI. The event
    passed in as a param checks for the startup event for the
    current application. This then triggers our connection to our
    redis cache via <FastApiRedisCache> instance.

    :rtype: Cache instance for application.
    """

    r = FastApiRedisCache()
    r.init(
        host_url=Config.REDIS_URL,
        prefix="supafast-cache",
        response_header="X-Supafast-Cache",
        ignore_arg_types=[Request, Response, SupabaseDB.supabase],
    )


@app.get("/")
def index():
    """
    Initial view or endpoint when visiting localhost:8000/

    :rtype: Welcome and instruction for walkthrough via readme or localhost:8000/docs
    """

    return {
        "👋 Hello": "Please refer to the readme\
 documentation for more or visit http://localhost:8000/docs"
    }


@app.get("/getResult")
def query():
    """
    Endpoing for testing data to be pulled from your supabase instance.

    :rtype: 1st row of consumer credit data.
    :endpoint: {
        "data": [
            {
                "clientid": 1,
                "income": 66155.9251,
                "age": 59,
                "loan": 8106.532131,
                "default": "0"
            }
        ],
    }
    """

    return SupabaseDB.supabase.table("credit_data").select("*").limit(1).execute()


@app.get("/cachedResults")
@cache_one_week()
async def get_defaults(request: Request, response: Response):
    """
    asynchronous function call for grabbing load default specific data
    by the first 10 rows of data from your supabase instance.

    :rtype: Loan defaults for individuals by a certain age or older.
    :endpoint:
    HTTP/1.1 200 OK
    cache-control: max-age=604321
    content-length: 894
    content-type: application/json
    date: Wed, 16 Feb 2022 21:53:56 GMT
    expires: Wed, 23 Feb 2022 21:45:57 GMT
    server: uvicorn
    x-supafast-cache: Hit

    "data=[{'clientid': 1, 'income': 66155.9251, 'age': 59, 'loan': 8106.532131, 'default': '0'},
    {'clientid': 2, 'income': 34415.15397, 'age': 48, 'loan': 6564.745018, 'default': '0'},
    {'clientid': 3, 'income': 57317.17006, 'age': 63, 'loan': 8020.953296, 'default': '0'},
    {'clientid': 4, 'income': 42709.5342, 'age': 46, 'loan': 6103.64226, 'default': '0'},
    {'clientid': 5, 'income': 66952.68885, 'age': 19, 'loan': 8770.099235, 'default': '1'},
    {'clientid': 6, 'income': 24904.06414, 'age': 57, 'loan': 15.49859844, 'default': '0'},
    {'clientid': 7, 'income': 48430.35961, 'age': 27, 'loan': 5722.581981, 'default': '0'},
    {'clientid': 8, 'income': 24500.14198, 'age': 33, 'loan': 2971.00331, 'default': '1'},
    {'clientid': 9, 'income': 40654.89254, 'age': 55, 'loan': 4755.82528, 'default': '0'},
    {'clientid': 10, 'income': 25075.87277, 'age': 40, 'loan': 1409.230371, 'default': '0'}] count=None"
    """

    data = SupabaseDB.supabase.table("credit_data").select("*").limit(10).execute()
    return json.dumps(data, indent=4)
