from typing import TypedDict
from postgrest._sync.client import SyncPostgrestClient


class MovieInsert(TypedDict):
    name: str
    description: str


def test_insert_accepts_typeddict():
    """
    TypedDict instances should be accepted by insert() without type errors.
    TypedDict is a subclass of dict at runtime so this should work fine.
    """
    client = SyncPostgrestClient("http://localhost:3000")
    builder = client.from_("movies")

    # This should not raise any type errors
    movie: MovieInsert = {"name": "Inception", "description": "A dream movie"}
    query = builder.insert(movie)

    # Verify the json body was set correctly
    assert query.request.json == movie


def test_insert_accepts_list_of_typeddict():
    """
    A list of TypedDict instances should also be accepted.
    """
    client = SyncPostgrestClient("http://localhost:3000")
    builder = client.from_("movies")

    movies: list[MovieInsert] = [
        {"name": "Inception", "description": "A dream movie"},
        {"name": "Interstellar", "description": "A space movie"},
    ]
    query = builder.insert(movies)

    assert query.request.json == movies


def test_insert_accepts_uuid_and_datetime():
    """
    UUID and Datetime objects should be properly serialized without TypeError.
    This asserts that PostgrestEncoder is working correctly beneath the hood when
    building the request configuration.
    """
    import uuid
    import datetime
    
    client = SyncPostgrestClient("http://localhost:3000")
    builder = client.from_("movies")

    movie = {
        "id": uuid.uuid4(),
        "created_at": datetime.datetime.now()
    }
    query = builder.insert(movie)
    
    # Validation that it works cleanly under the hood when formatting the API request. 
    import json
    from postgrest.base_request_builder import PostgrestEncoder
    
    # Should not raise a TypeError: Object of type <...> is not JSON serializable
    assert json.dumps(query.request.json, cls=PostgrestEncoder) is not None
