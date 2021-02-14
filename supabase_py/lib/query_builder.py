from postgrest_py.client import PostgrestClient
from .realtime_client import SupabaseRealtimeClient


class SupabaseQueryBuilder(PostgrestClient):
    def __init__(self, url, headers, schema, realtime, table):
        """
        Subscribe to realtime changes in your database.

        Parameters
        ----------
        url
            Base URL of the Supabase Instance that the client library is acting on
        headers
            authentication/authorization headers which are passed in.
        schema
            schema of table that we are building queries for
        realtime
            realtime-py client
        table
            Name of table to look out for operations on
        Returns
        -------
        None
        """
        super().__init__(url)
        self._subscription = SupabaseRealtimeClient(realtime, schema, table)
        self._realtime = realtime

    def on(self, event, callback):
        """Subscribe to realtime changes in your database.

        Parameters
        ----------
        event
            the event which we are looking out for.
        callback
            function to be execute when the event is received

        Returns
        -------
        SupabaseRealtimeClient
        Returns an instance of a SupabaseRealtimeClient to allow for chaining.
        """
        if not self._realtime.connected:
            self._realtime.connect()
        return self._subscription.on(event, callback)
