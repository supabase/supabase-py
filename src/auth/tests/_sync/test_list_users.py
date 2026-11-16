from typing import Any

from httpx import Client, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import HttpxSession

from supabase_auth import SyncSupabaseAuthAdmin


def user(index: int) -> dict[str, Any]:
    return {
        "id": f"00000000-0000-0000-0000-{index:012d}",
        "email": f"user{index}@example.com",
        "aud": "authenticated",
        "app_metadata": {},
        "user_metadata": {},
        "created_at": "2026-01-01T00:00:00Z",
    }


def pagination_headers(page: int, last_page: int, total: int) -> dict[str, str]:
    links = []
    if page < last_page:
        links.append(f'</admin/users?page={page + 1}&per_page=2>; rel="next"')
    links.append(f'</admin/users?page={last_page}&per_page=2>; rel="last"')
    return {"x-total-count": str(total), "link": ", ".join(links)}


def admin_client(
    pages: list[list[dict[str, Any]]],
) -> tuple[SyncSupabaseAuthAdmin, list[Request]]:
    requests: list[Request] = []
    total = sum(len(page) for page in pages)

    def handler(request: Request) -> Response:
        requests.append(request)
        page = int(request.url.params.get("page") or "1")
        return Response(
            200,
            json={"users": pages[page - 1], "aud": "authenticated"},
            headers=pagination_headers(page, len(pages), total),
        )

    client = SyncSupabaseAuthAdmin(
        url="https://example.supabase.co/auth/v1",
        http_session=HttpxSession(client=Client(transport=MockTransport(handler))),
    )
    return client, requests


def test_list_users_returns_the_pagination_information() -> None:
    client, requests = admin_client([[user(1), user(2)], [user(3), user(4)], [user(5)]])

    response = client.list_users(page=2, per_page=2)

    assert [request.url.params["page"] for request in requests] == ["2"]
    assert [item.email for item in response.users] == [
        "user3@example.com",
        "user4@example.com",
    ]
    assert response.aud == "authenticated"
    assert response.next_page == 3
    assert response.last_page == 3
    assert response.total == 5


def test_list_users_on_the_last_page_has_no_next_page() -> None:
    client, _ = admin_client([[user(1), user(2)], [user(3)]])

    response = client.list_users(page=2, per_page=2)

    assert response.next_page is None
    assert response.last_page == 2
    assert response.total == 3


def test_list_users_without_pagination_headers() -> None:
    def handler(_request: Request) -> Response:
        return Response(200, json={"users": [user(1)]})

    client = SyncSupabaseAuthAdmin(
        url="https://example.supabase.co/auth/v1",
        http_session=HttpxSession(client=Client(transport=MockTransport(handler))),
    )

    response = client.list_users()

    assert len(response.users) == 1
    assert response.next_page is None
    assert response.last_page == 0
    assert response.total == 0


def test_iter_users_fetches_every_page_lazily() -> None:
    client, requests = admin_client([[user(1), user(2)], [user(3), user(4)], [user(5)]])

    iterator = client.iter_users(per_page=2)
    first = next(iterator)

    assert first.email == "user1@example.com"
    assert len(requests) == 1

    rest = [item.email for item in iterator]

    assert rest == [
        "user2@example.com",
        "user3@example.com",
        "user4@example.com",
        "user5@example.com",
    ]
    assert [
        (request.url.params["page"], request.url.params["per_page"])
        for request in requests
    ] == [("1", "2"), ("2", "2"), ("3", "2")]


def test_iter_users_stops_on_an_empty_page_with_a_next_link() -> None:
    client, requests = admin_client([[], [user(1)]])

    assert next(client.iter_users(), None) is None
    assert len(requests) == 1


def test_iter_users_stops_when_the_next_page_does_not_advance() -> None:
    requests: list[Request] = []

    def handler(request: Request) -> Response:
        requests.append(request)
        return Response(
            200,
            json={"users": [user(1)]},
            headers={"link": '</admin/users?page=1>; rel="next"'},
        )

    client = SyncSupabaseAuthAdmin(
        url="https://example.supabase.co/auth/v1",
        http_session=HttpxSession(client=Client(transport=MockTransport(handler))),
    )

    assert [item.email for item in client.iter_users()] == ["user1@example.com"]
    assert len(requests) == 1


def test_list_users_ignores_a_non_numeric_total() -> None:
    def handler(_request: Request) -> Response:
        return Response(
            200, json={"users": [user(1)]}, headers={"x-total-count": "unknown"}
        )

    client = SyncSupabaseAuthAdmin(
        url="https://example.supabase.co/auth/v1",
        http_session=HttpxSession(client=Client(transport=MockTransport(handler))),
    )

    response = client.list_users()

    assert response.total == 0
