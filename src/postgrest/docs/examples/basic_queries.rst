Getting Started
===============

We connect to the API and authenticate, and fetch some data.

.. code-block:: python
    :linenos:

    import asyncio
    from postgrest import AsyncPostgrestClient

    async def main():
        async with AsyncPostgrestClient("http://localhost:3000") as client:
            client.auth("Bearer <token>")
            r = await client.from_("countries").select("*").execute()
            countries = r.data

    asyncio.run(main())


**CRUD**

.. code-block:: python

    await client.from_("countries").insert({ "name": "Việt Nam", "capital": "Hà Nội" }).execute()


.. code-block:: python

    r = await client.from_("countries").select("id", "name").execute()
    countries = r.data


.. code-block:: python

    await client.from_("countries").update({"capital": "Hà Nội"}).eq("name", "Việt Nam").execute()

.. code-block:: python

    await client.from_("countries").delete().eq("name", "Việt Nam").execute()

**Calling RPCs**

.. code-block:: python

    await client.rpc("foo").execute()

.. code-block:: python

    await client.rpc("bar", {"arg1": "value1", "arg2": "value2"}).execute()


**Closing the connection**

Once you have finished running your queries, close the connection:

.. code-block:: python

    await client.aclose()


You can also use the client with a context manager, which will close the client for you.

.. code-block:: python

    async with AsyncPostgrestClient("url") as client:
        # run queries
    # the client is closed when the async with block ends
