Responses
=========

Once a query is run, the library parses the server's response into an APIResponse object.

.. autoclass:: postgrest.APIResponse
    :members:

For callers that prefer to handle failures without exceptions, ``execute_result``
returns a structured result for both successful and unsuccessful HTTP responses.

.. autoclass:: postgrest.ExecuteResult
    :members:
