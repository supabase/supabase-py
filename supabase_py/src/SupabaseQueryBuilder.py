from postgrest_py.request_builder import RequestBuilder


class SupabaseQueryBuilder(RequestBuilder):
    def __init__(self, session: AsyncClient, path: str):
        super().__init__(session, path)
        pass

    def on(self):
        pass
