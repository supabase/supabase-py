from typing import Optional

from supabase_auth.types import AuthChangeEvent, Session

from .clients import auth_client


def test_auth_state_change_callback_can_unsubscribe_during_notification() -> None:
    client = auth_client()
    received: list[tuple[str, AuthChangeEvent]] = []

    def unsubscribe_on_event(
        event: AuthChangeEvent, session: Optional[Session]
    ) -> None:
        received.append(("once", event))
        subscription.unsubscribe()

    subscription = client.on_auth_state_change(unsubscribe_on_event)
    client.on_auth_state_change(
        lambda event, session: received.append(("always", event))
    )

    client.sign_out()
    assert received == [("once", "SIGNED_OUT"), ("always", "SIGNED_OUT")]

    client.sign_out()
    assert received == [
        ("once", "SIGNED_OUT"),
        ("always", "SIGNED_OUT"),
        ("always", "SIGNED_OUT"),
    ]
