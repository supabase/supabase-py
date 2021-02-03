from postgrest_py.client import PostgrestClient
from .supabase_realtime_client import SupabaseRealtimeClient
from typing import Callable


class SupabaseQueryBuilder(PostgrestClient):
    def __init__(self, url, headers, schema, realtime, table):
        super.__init__(url, schema)
        self._subscription = SupabaseRealtimeClient(realtime, schema, table)
        self._realtime = realtime

    def on(self, event, callback):
        """
        Subscribe to realtime changes in your database
        """
        if not self._realtime.connected:
            self._realtime.connect()
        return self._subscription.on(event, callback)
