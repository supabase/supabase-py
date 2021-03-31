import requests
from requests import HTTPError


class StorageBucketApi:

    def __init__(self, url, headers):
        self.url = url
        self.headers = headers

    def list_buckets(self):
        """Retrieves the details of all Storage buckets within an existing product."""
        try:
            response = requests.get(f"{self.url}/bucket", headers=self.headers)

            # If the response was successful, no Exception will be raised
            response.raise_for_status()
        except HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')  # Python 3.6
        except Exception as err:
            print(f'Other error occurred: {err}')  # Python 3.6
        else:
            return response.json()

    def get_bucket(self, id: str):
        """Retrieves the details of an existing Storage bucket.

        Parameters
        ----------
        id
            The unique identifier of the bucket you would like to retrieve.
        """
        try:
            response = requests.get(f"{self.url}/bucket/{id}", headers=self.headers)

            # If the response was successful, no Exception will be raised
            response.raise_for_status()
        except HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')  # Python 3.6
        except Exception as err:
            print(f'Other error occurred: {err}')  # Python 3.6
        else:
            return response.json()

    def create_bucket(self, id: str):
        """Creates a new Storage bucket

        Parameters
        ----------
        id
            A unique identifier for the bucket you are creating.
        """
        try:
            response = requests.post(f"{self.url}/bucket", data={"id": id}, headers=self.headers)

            # If the response was successful, no Exception will be raised
            response.raise_for_status()
        except HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')  # Python 3.6
        except Exception as err:
            print(f'Other error occurred: {err}')  # Python 3.6
        else:
            return response.json()

    def empty_bucket(self, id: str):
        """Removes all objects inside a single bucket.

        Parameters
        ----------
        id
            The unique identifier of the bucket you would like to empty.
        """
        try:
            response = requests.post(f"{self.url}/bucket/{id}/empty", data={}, headers=self.headers)

            # If the response was successful, no Exception will be raised
            response.raise_for_status()
        except HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')  # Python 3.6
        except Exception as err:
            print(f'Other error occurred: {err}')  # Python 3.6
        else:
            return response

    def delete_bucket(self, id: str):
        """Deletes an existing bucket. A bucket can't be deleted with existing objects inside it.You must first
        `empty()` the bucket.

        Parameters
        ----------
        id
            The unique identifier of the bucket you would like to delete.
        """
        try:
            response = requests.delete(f"{self.url}/bucket/{id}", data={}, headers=self.headers)

            # If the response was successful, no Exception will be raised
            response.raise_for_status()
        except HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')  # Python 3.6
        except Exception as err:
            print(f'Other error occurred: {err}')  # Python 3.6
        else:
            return response
