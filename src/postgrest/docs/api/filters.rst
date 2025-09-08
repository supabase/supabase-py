Filter Builder
==============

This is a kind of `request builder <Request Builders>`_. It contains all the methods used to
filter data during queries.

.. note::
    In the source code, there are separate AsyncFilterRequestBuilders and SyncFilterRequestBuilders.
    These classes are otherwise exactly the same, and provide the same interface.

.. warning::
    These classes are not meant to be constructed by the user.

.. tip::
    The full list of supported filter operators are on the `PostgREST documentation <https://postgrest.org/en/stable/api.html#operators>`_

.. tip::
    All the filter methods return a modified instance of the filter builder, allowing fluent chaining of filters.


.. autoclass:: postgrest.AsyncFilterRequestBuilder
    :members:
    :undoc-members:
    :inherited-members:
    :member-order: bysource

.. autoclass:: postgrest.SyncFilterRequestBuilder
    :members:
    :undoc-members:
    :inherited-members:
    :member-order: bysource
