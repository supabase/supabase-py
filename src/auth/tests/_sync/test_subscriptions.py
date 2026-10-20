from supabase_auth import SyncSupabaseAuthClient
from supabase_auth.types import AuthChangeEvent, Session


def test_auth_state_change_callback_can_unsubscribe_during_notification(
    auth_client: SyncSupabaseAuthClient,
) -> None:
    received: list[tuple[str, AuthChangeEvent]] = []

    def unsubscribe_on_event(event: AuthChangeEvent, session: Session | None) -> None:
        received.append(("once", event))
        subscription.unsubscribe()

    subscription = auth_client.on_auth_state_change(unsubscribe_on_event)
    auth_client.on_auth_state_change(
        lambda event, session: received.append(("always", event))
    )

    auth_client.sign_out()
    assert received == [("once", "SIGNED_OUT"), ("always", "SIGNED_OUT")]

    auth_client.sign_out()
    assert received == [
        ("once", "SIGNED_OUT"),
        ("always", "SIGNED_OUT"),
        ("always", "SIGNED_OUT"),
    ]
