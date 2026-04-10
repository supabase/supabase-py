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
