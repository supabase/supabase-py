from postgrest._sync.request_builder import SyncSelectRequestBuilder
from postgrest._sync.client import SyncPostgrestClient

def test_query_builder_is_immutable():
    """
    Reusing a base query should not carry over filters from previous uses.
    """
    client = SyncPostgrestClient("http://localhost:3000")

    base_query = client.from_("users").select("*")
    query_a = base_query.eq("role", "admin")
    query_b = base_query.eq("role", "user")

    # The params on query_a and query_b should be independent
    assert query_a.request.params != query_b.request.params

    # The base query should be untouched
    assert base_query.request.params != query_a.request.params
    assert base_query.request.params != query_b.request.params
