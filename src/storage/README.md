# Storage-py

Python Client library to interact with Supabase Storage.



## How to use

As it takes some effort to get the headers. We suggest that you use the storage functionality through the main [Supabase Python Client](https://github.com/supabase-community/supabase-py)


```python3
from storage3 import AsyncStorageClient

url = "https://<your_supabase_id>.supabase.co/storage/v1"
key = "<your api key>"
headers = {"apiKey": key, "Authorization": f"Bearer {key}"}

storage_client = AsyncStorageClient(url, headers)

async def get_buckets():
  await storage_client.list_buckets()
```

### Uploading files
When uploading files, make sure to set the correct mimetype by using the `file_options` argument:
```py
async def file_upload():
  await storage_client.from_("bucket").upload("/folder/file.png", file_object, {"content-type": "image/png"})
```
If no mime type is given, the default `text/plain` will be used.
