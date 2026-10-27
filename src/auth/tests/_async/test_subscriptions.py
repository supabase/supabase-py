from supabase_auth import AsyncSupabaseAuthClient
from supabase_auth.types import AuthChangeEvent, Session


async def test_auth_state_change_callback_can_unsubscribe_during_notification(
    auth_client: AsyncSupabaseAuthClient,
) -> None:
    received: list[tuple[str, AuthChangeEvent]] = []

    def unsubscribe_on_event(event: AuthChangeEvent, session: Session | None) -> None:
        received.append(("once", event))
        subscription.unsubscribe()

    subscription = auth_client.on_auth_state_change(unsubscribe_on_event)
    auth_client.on_auth_state_change(
        lambda event, session: received.append(("always", event))
    )

    await auth_client.sign_out()
    assert received == [("once", "SIGNED_OUT"), ("always", "SIGNED_OUT")]

    await auth_client.sign_out()
    assert received == [
        ("once", "SIGNED_OUT"),
        ("always", "SIGNED_OUT"),
        ("always", "SIGNED_OUT"),
    ]

    subscription.unsubscribe()
