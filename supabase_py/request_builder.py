from httpx import AsyncClient
from postgrest_py.request_builder import RequestBuilder


class SupabaseRequestBuilder(RequestBuilder):
    def __init__(self, session: AsyncClient, path: str):
        super().__init__(session, path)
