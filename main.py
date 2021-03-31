import os
from supabase_py import create_client, Client
import asyncio

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")  # service key
supabase: Client = create_client(url, key)
loop = asyncio.new_event_loop()

storage = supabase.storage()
storage_file = storage.StorageFileApi("poll")  # id of the bucket
url = storage_file.create_signed_url("poll3o/test2.txt", 80)  # signed url
loop.run_until_complete(storage_file.download("poll3o/test2.txt")) #upload or download
loop.run_until_complete(storage_file.upload("poll3o/test2.txt","path_file_upload"))
list_buckets = storage.list_buckets()
list_files = storage_file.list("pollo")
print("ls")
if __name__ == '__main__':
    pass