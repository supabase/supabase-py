import logging
from typing import Dict

logging.basicConfig(
    format="%(asctime)s:%(levelname)s - %(message)s", level=logging.INFO
)

try:
    import vecs

    VEC_INSTALLED = True
except ImportError:
    VEC_INSTALLED = False


class VecsClient:
    def __init__(self, connection_string: str):
        self.admin = VecsAdminClient(connection_string)


class VecsAdminClient:
    def __init__(self, connection_string: str):
        if not VEC_INSTALLED:
            logging.warn(
                "vecs library is not installed. Please install it to use this vecs client. You can install it by running `pip install supabase[vecs]`"
            )
        else:
            self._client = vecs.create_client(connection_string=connection_string)
            self._collections: Dict[str, vecs.Collection] = dict()

    def _vecs_installed(self):
        if not VEC_INSTALLED:
            logging.error(
                "vecs library is not installed. This method will not work. Please install it to use this vecs client. You can install it by running `pip install supabase[vecs]`"
            )
            return False
        else:
            return True

    def get_or_create_collection(
        self,
        name: str,
        *,
        dimension: int | None = None,
        adapter=None,
    ):
        if not self._vecs_installed():
            return None
        if name in self._collections:
            return self._collections.get(name)
        else:
            collection = self._client.get_or_create_collection(
                name=name,
                dimension=dimension,
                adapter=adapter,
            )
            self._collections[name] = collection
            self.__setattr__(name, collection)
            return collection

    def delete_collection(self, name: str):
        if not self._vecs_installed():
            return None
        if name in self._collections:
            self._collections.pop(name)
            self.__delattr__(name)
            return self._client.delete_collection(name)
        else:
            return self._client.delete_collection(name)

    def list_collections(self):
        if not self._vecs_installed():
            return None
        collections = self._client.list_collections()
        for collection in collections:
            self._collections[collection.name] = collection
            self.__setattr__(collection.name, collection)
        return collections

    def __getattr__(self, name):
        if not self._vecs_installed():
            return None
        if name in self._collections:
            return self._collections.get(name)
        else:
            try:
                collection = self._client.get_collection(name)
                self._collections[name] = collection
                self.__setattr__(name, collection)
                return collection
            except vecs.exc.CollectionNotFound:
                logging.error(f"Collection {name} not found")
                return None

    def __del__(self):
        if not VEC_INSTALLED:
            return None
        self._client.disconnect()
