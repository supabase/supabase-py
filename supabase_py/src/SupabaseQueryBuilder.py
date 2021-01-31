from postgrest_py.client import PostgrestClient
from .SupabaseRealtimeClient import SupabaseRealtimeClient


class SupabaseQueryBuilder(PostgrestClient):
    def __init__(self, url, headers, schema, realtime, table):
        super.__init__(url, {headers, schema})
        self._subscription = SupabaseRealtimeClient(realtime, schema, table)
        self._realtime = realtime

    def on(self, event, callback):
        """
        Subscribe to realtime changes in your database
        """
        pass
