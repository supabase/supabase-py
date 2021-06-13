import requests
from requests import HTTPError


class StorageFileApi:
    def __init__(self, url: str, headers: dict, bucket_id: str):
        """
        Parameters
        ----------
        url
            base url for all the operation
        headers
            the base authentication headers
        bucket_id
            the id of the bucket that we want to access, you can get the list of buckets with the SupabaseStorageClient.list_buckets()
        """
        self.url = url
        self.headers = headers
        self.bucket_id = bucket_id
        # self.loop = asyncio.get_event_loop()
        # self.replace = replace
        pass

    def create_signed_url(self, path: str, expires_in: int):
        """
        Parameters
        ----------
        path
            file path to be downloaded, including the current file name.
        expires_in
            number of seconds until the signed URL expires.
        """
        try:
            _path = self._get_final_path(path)
            print(f"{self.url}/object/sign/{_path}")
            response = requests.post(
                f"{self.url}/object/sign/{_path}",
                json={"expiresIn": str(expires_in)},
                headers=self.headers,
            )
            data = response.json()
            print(data)
            data["signedURL"] = f"{self.url}{data['signedURL']}"
            response.raise_for_status()
        except HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")  # Python 3.6
        except Exception as err:
            print(f"Other error occurred: {err}")  # Python 3.6
        else:
            return data

    def move(self, from_path: str, to_path: str):
        pass

    def _get_final_path(self, path: str):
        return f"{self.bucket_id}/{path}"
