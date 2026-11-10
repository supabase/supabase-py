from supabase_auth import AsyncSupabaseAuthClient
from supabase_auth.types import AuthChangeEvent, AuthStateChange, SignOutReason


async def test_listener_receives_the_initial_session_once(
    auth_client_with_session: AsyncSupabaseAuthClient,
) -> None:
    changes: list[AuthStateChange] = []

    auth_client_with_session.on_auth_state_change(changes.append)

    assert len(changes) == 1
    assert changes[0].event is AuthChangeEvent.INITIAL_SESSION
    assert changes[0].session == await auth_client_with_session.get_session()
    assert changes[0].sign_out_reason is None


async def test_listener_without_a_session_receives_an_empty_initial_session(
    auth_client: AsyncSupabaseAuthClient,
) -> None:
    changes: list[AuthStateChange] = []

    auth_client.on_auth_state_change(changes.append)

    assert changes == [AuthStateChange(AuthChangeEvent.INITIAL_SESSION)]


async def test_sign_out_reports_a_user_initiated_sign_out(
    auth_client_with_session: AsyncSupabaseAuthClient,
) -> None:
    changes: list[AuthStateChange] = []
    auth_client_with_session.on_auth_state_change(changes.append)

    await auth_client_with_session.sign_out()

    assert changes[-1] == AuthStateChange(
        AuthChangeEvent.SIGNED_OUT,
        sign_out_reason=SignOutReason.USER_INITIATED,
    )


async def test_auth_state_change_callback_can_unsubscribe_during_notification(
    auth_client: AsyncSupabaseAuthClient,
) -> None:
    received: list[tuple[str, AuthChangeEvent]] = []

    def unsubscribe_on_sign_out(change: AuthStateChange) -> None:
        received.append(("once", change.event))
        if change.event is AuthChangeEvent.SIGNED_OUT:
            subscription.unsubscribe()

    subscription = auth_client.on_auth_state_change(unsubscribe_on_sign_out)
    auth_client.on_auth_state_change(
        lambda change: received.append(("always", change.event))
    )
    received.clear()

    await auth_client.sign_out()
    assert received == [
        ("once", AuthChangeEvent.SIGNED_OUT),
        ("always", AuthChangeEvent.SIGNED_OUT),
    ]

    await auth_client.sign_out()
    assert received == [
        ("once", AuthChangeEvent.SIGNED_OUT),
        ("always", AuthChangeEvent.SIGNED_OUT),
        ("always", AuthChangeEvent.SIGNED_OUT),
    ]

    subscription.unsubscribe()
