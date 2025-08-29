Logging Requests
================

While debugging, you might want to see the API requests that are being sent for every query.
To do this, just set the logging level to "DEBUG":

.. code-block:: python
    :linenos:

    from logging import basicConfig, DEBUG
    from postgrest import SyncPostgrestClient

    basicConfig(level=DEBUG)

    client  = SyncPostgrestClient(...)

    client.from_("test").select("*").eq("a", "b").execute()
    client.from_("test").select("*").eq("foo", "bar").eq("baz", "spam").execute()

Output:

.. code-block::

    DEBUG:httpx._client:HTTP Request: GET https://<URL>/rest/v1/test?select=%2A&a=eq.b "HTTP/1.1 200 OK"
    DEBUG:httpx._client:HTTP Request: GET https://<URL>/rest/v1/test?select=%2A&foo=eq.bar&baz=eq.spam "HTTP/1.1 200 OK"
