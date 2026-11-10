from __future__ import annotations

import asyncio
import logging
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from functools import partial
from typing import TYPE_CHECKING, Any, Self
from uuid import uuid4

from supabase_utils.http.headers import Headers
from supabase_utils.http.io import (
    AsyncHttpIO,
    HttpMethod,
    SyncHttpIO,
    handle_http_io,
)
from supabase_utils.http.query import URLQuery
from supabase_utils.http.request import EmptyRequest, JSONRequest
from yarl import URL

from .constants import (
    EXPIRY_MARGIN,
    MAX_RETRIES,
    RETRY_BASE_DELAY,
    RETRY_MAX_DELAY,
    STORAGE_KEY,
)
from .errors import (
    AuthApiError,
    AuthRetryableError,
    AuthSessionMissingError,
    AuthUnknownError,
)
from .helpers import parse_auth_response, parse_user_response
from .timer import _AsyncTimer, _SyncTimer
from .types import (
    AuthChangeEvent,
    AuthStateChange,
    Session,
    SignOutReason,
    Subscription,
    UserResponse,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine
    from types import TracebackType


logger = logging.getLogger(__name__)


def _retry_delay(attempt: int) -> float:
    return min(RETRY_BASE_DELAY * 2.0 ** (attempt - 1), RETRY_MAX_DELAY)


def _is_terminal_refresh_error(error: BaseException) -> bool:
    """Whether a failed refresh means the refresh token is no longer valid.

    Only a definite rejection by the auth service, a 4xx other than a rate
    limit, signs the user out. A transport error, a 429 or 5xx (both an
    `AuthRetryableError`) and a response that could not be parsed say nothing
    about the token, so the session is kept and refreshed again later.
    """
    return isinstance(error, AuthApiError) and not isinstance(error, AuthRetryableError)


def _consume_exception(task: asyncio.Task[Any]) -> None:
    """Mark the exception of a shared refresh as retrieved, so a refresh every
    waiter was cancelled away from does not log it as unretrieved."""
    if not task.cancelled():
        task.exception()


class AsyncSupportedStorage(ABC):
    @abstractmethod
    async def get_item(self, key: str) -> str | None: ...  # pragma: no cover

    @abstractmethod
    async def set_item(self, key: str, value: str) -> None: ...  # pragma: no cover

    @abstractmethod
    async def remove_item(self, key: str) -> None: ...  # pragma: no cover


class AsyncMemoryStorage(AsyncSupportedStorage):
    def __init__(self) -> None:
        self.storage: dict[str, str] = {}

    async def get_item(self, key: str) -> str | None:
        if key in self.storage:
            return self.storage[key]
        return None

    async def set_item(self, key: str, value: str) -> None:
        self.storage[key] = value

    async def remove_item(self, key: str) -> None:
        if key in self.storage:
            del self.storage[key]


@dataclass
class _SessionManagerCommon[HttpIO: (SyncHttpIO, AsyncHttpIO)]:
    """
    Common methods shared between sync and async implementations
    of the session manager.
    """

    base_url: URL
    executor: HttpIO
    default_headers: Headers
    state_change_emitters: dict[str, Subscription]
    storage_key: str = field(default=STORAGE_KEY, kw_only=True)
    auto_refresh_token: bool = field(default=True, kw_only=True)
    _current_session: Session | None = field(default=None, init=False, repr=False)
    """The session as last read from or written to the storage."""
    _failed_refreshes: int = field(default=0, init=False, repr=False)
    """Consecutive background refreshes that failed without a rejection."""

    def _refresh_access_token(self, refresh_token: str) -> HttpMethod[Session]:
        response = yield JSONRequest(
            method="POST",
            path=["token"],
            query=URLQuery.from_mapping({"grant_type": "refresh_token"}),
            body={"refresh_token": refresh_token},
        )
        session = parse_auth_response(response).session
        if session is None:
            raise AuthUnknownError(
                "Unexpected error: the refreshed session is missing",
                status_code=response.status,
                response=response,
            )
        return session

    @handle_http_io
    def refresh_access_token(self, refresh_token: str) -> HttpMethod[Session]:
        return self._refresh_access_token(refresh_token)

    def _get_user(self, jwt: str) -> HttpMethod[UserResponse]:
        """
        Gets the current user details if there is an existing session.

        Takes in an optional access token `jwt`. If no `jwt` is provided,
        `get_user()` will attempt to get the `jwt` from the current session.
        """
        response = yield EmptyRequest(
            method="GET",
            path=["user"],
            headers=Headers.from_mapping({"authorization": f"Bearer {jwt}"}),
        )
        return parse_user_response(response)

    @handle_http_io
    def get_user(self, jwt: str) -> HttpMethod[UserResponse]:
        return self._get_user(jwt)

    def parse_valid_session(
        self,
        raw_session: str | None,
    ) -> Session | None:
        if not raw_session:
            return None
        try:
            session = Session.model_validate_json(raw_session)
            if session.expires_at is None:
                return None
            return session
        except Exception:
            return None

    def subscribe(self, callback: Callable[[AuthStateChange], None]) -> Subscription:
        """Register `callback` and deliver `INITIAL_SESSION` to it, with the
        session the client knows of at this moment."""
        unique_id = str(uuid4())

        def _unsubscribe() -> None:
            self.state_change_emitters.pop(unique_id, None)

        subscription = Subscription(
            id=unique_id,
            callback=callback,
            unsubscribe=_unsubscribe,
        )
        self.state_change_emitters[unique_id] = subscription
        self._deliver(
            subscription,
            AuthStateChange(AuthChangeEvent.INITIAL_SESSION, self._current_session),
        )
        return subscription

    def notify_all_subscribers(self, change: AuthStateChange) -> None:
        for subscription in list(self.state_change_emitters.values()):
            self._deliver(subscription, change)

    @staticmethod
    def _deliver(subscription: Subscription, change: AuthStateChange) -> None:
        try:
            subscription.callback(change)
        except Exception:
            logger.exception("auth state change callback raised for %s", change.event)

    @staticmethod
    def _is_expiring(session: Session) -> bool:
        """Whether the access token expires within `EXPIRY_MARGIN` seconds."""
        if session.expires_at is None:
            return False
        return session.expires_at <= time.time() + EXPIRY_MARGIN

    @staticmethod
    def _refresh_delay(expires_at: int) -> float:
        """Seconds until a session that expires at `expires_at` should be
        refreshed: `EXPIRY_MARGIN` before it expires, or half a second before
        when it is already closer than that."""
        expires_in = expires_at - time.time()
        margin = EXPIRY_MARGIN if expires_in > EXPIRY_MARGIN else 0.5
        return expires_in - margin

    def _signed_out(self, reason: SignOutReason) -> AuthStateChange:
        return AuthStateChange(AuthChangeEvent.SIGNED_OUT, sign_out_reason=reason)

    def _retry_in(self, error: Exception) -> float | None:
        """Seconds until a failed background refresh is tried again, or None
        when the failure was final or the retries are used up."""
        if _is_terminal_refresh_error(error):
            return None
        self._failed_refreshes += 1
        if self._failed_refreshes >= MAX_RETRIES:
            logger.warning(
                "giving up on refreshing the session after %d attempts",
                self._failed_refreshes,
                exc_info=error,
            )
            return None
        delay = _retry_delay(self._failed_refreshes)
        logger.debug(
            "refreshing the session failed, retrying in %.1f seconds",
            delay,
            exc_info=error,
        )
        return delay


@dataclass
class _AsyncSessionManager(_SessionManagerCommon[AsyncHttpIO]):
    storage: AsyncSupportedStorage
    refresh_token_timer: _AsyncTimer | None = None
    _refresh_task: asyncio.Task[Session] | None = field(
        default=None, init=False, repr=False
    )
    """The refresh in flight, shared by every caller that needs one."""

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self._cancel_refresh_timer()
        task, self._refresh_task = self._refresh_task, None
        if task is not None:
            task.cancel()

    async def __aenter__(self) -> Self:
        return self

    async def load_session(self) -> Session | None:
        """
        Returns the stored session without refreshing it.

        A stored value that is not a valid session is removed, with a
        `SIGNED_OUT` notification.
        """
        raw_session = await self.storage.get_item(self.storage_key)
        if not raw_session:
            self._current_session = None
            return None
        session = self.parse_valid_session(raw_session)
        if session is None:
            await self._sign_out_locally(SignOutReason.SESSION_MISSING)
            return None
        self._current_session = session
        return session

    async def get_session(self) -> Session | None:
        """
        Returns the session, refreshing it if necessary.

        The session returned can be null if the session is not detected which
        can happen in the event a user is not signed-in or has logged out.

        Concurrent calls share one refresh. A refresh the auth service rejects
        removes the session, notifies `SIGNED_OUT` and raises the error.
        """
        session = await self.load_session()
        if session is None or not self._is_expiring(session):
            return session
        try:
            return await self._single_flight(
                partial(self._refresh_stored_session, only_if_expiring=True)
            )
        except AuthSessionMissingError:
            return None

    async def get_session_or_raise(self) -> Session:
        session = await self.get_session()
        if not session:
            raise AuthSessionMissingError
        return session

    async def refresh_session(self) -> Session:
        """Refresh the stored session whether or not it is expiring, sharing
        a refresh that is already in flight. Raises `AuthSessionMissingError`
        when there is no stored session."""
        return await self._single_flight(self._refresh_stored_session)

    async def call_refresh_token(self, refresh_token: str) -> Session:
        """Refresh the session with `refresh_token`, sharing a refresh that is
        already in flight."""
        return await self._single_flight(partial(self._refresh_with, refresh_token))

    async def save_session(self, session: Session) -> None:
        if session.expires_at is None:
            return
        self._current_session = session
        await self.storage.set_item(self.storage_key, session.model_dump_json())
        self._schedule_refresh(
            self._refresh_delay(session.expires_at), session.refresh_token
        )

    async def remove_session(self) -> None:
        await self.storage.remove_item(self.storage_key)
        self._current_session = None
        self._cancel_refresh_timer()

    async def recover_and_refresh(self) -> None:
        session = await self.load_session()
        if session is None:
            return
        if not self._is_expiring(session):
            await self.save_session(session)
            self.notify_all_subscribers(
                AuthStateChange(AuthChangeEvent.SIGNED_IN, session)
            )
            return
        if not session.refresh_token:
            await self._sign_out_locally(SignOutReason.SESSION_MISSING)
            return
        if self.auto_refresh_token:
            await self._refresh_or_retry()

    async def _sign_out_locally(self, reason: SignOutReason) -> None:
        await self.remove_session()
        self.notify_all_subscribers(self._signed_out(reason))

    async def _single_flight(
        self, refresh: Callable[[], Coroutine[Any, Any, Session]]
    ) -> Session:
        """Run `refresh` unless a refresh is already in flight, and return the
        result of whichever runs. The refresh is its own task, so cancelling
        one waiter does not cancel it for the others."""
        task = self._refresh_task
        if task is None or task.done():
            task = self._refresh_task = asyncio.create_task(refresh())
            task.add_done_callback(_consume_exception)
        return await asyncio.shield(task)

    async def _refresh_stored_session(
        self, *, only_if_expiring: bool = False, scheduled_for: str | None = None
    ) -> Session:
        """Refresh the stored session with its own refresh token.

        The stored session is read again first, so a caller that waited for
        another refresh sees the session that refresh saved. It is returned
        as is when it is not expiring and `only_if_expiring` is set, or when
        its refresh token is no longer `scheduled_for`, the token the refresh
        was scheduled for.
        """
        session = await self.load_session()
        if session is None:
            raise AuthSessionMissingError
        if not session.refresh_token:
            await self._sign_out_locally(SignOutReason.SESSION_MISSING)
            raise AuthSessionMissingError
        if only_if_expiring and not self._is_expiring(session):
            return session
        if scheduled_for is not None and session.refresh_token != scheduled_for:
            return session
        return await self._refresh_with(session.refresh_token)

    async def _refresh_with(self, refresh_token: str) -> Session:
        if not refresh_token:
            raise AuthSessionMissingError
        try:
            session = await self.refresh_access_token(refresh_token)
        except Exception as error:
            if _is_terminal_refresh_error(error):
                await self._sign_out_locally(SignOutReason.SESSION_EXPIRED)
            raise
        self._failed_refreshes = 0
        await self.save_session(session)
        self.notify_all_subscribers(
            AuthStateChange(AuthChangeEvent.TOKEN_REFRESHED, session)
        )
        return session

    async def _auto_refresh_tick(self, refresh_token: str | None) -> None:
        # The timer that fired is spent. Forgetting it here keeps the refresh
        # below from cancelling the very task that runs it.
        self.refresh_token_timer = None
        await self._refresh_or_retry(scheduled_for=refresh_token)

    async def _refresh_or_retry(self, *, scheduled_for: str | None = None) -> None:
        try:
            await self._single_flight(
                partial(self._refresh_stored_session, scheduled_for=scheduled_for)
            )
        except AuthSessionMissingError:
            return
        except Exception as error:
            delay = self._retry_in(error)
            if delay is not None:
                self._schedule_refresh(delay, None)

    def _schedule_refresh(self, seconds: float, refresh_token: str | None) -> None:
        """Refresh the stored session in `seconds`, unless its refresh token
        is no longer `refresh_token` by then. None refreshes it regardless."""
        self._cancel_refresh_timer()
        if seconds <= 0 or not self.auto_refresh_token:
            return
        self.refresh_token_timer = _AsyncTimer(
            seconds, partial(self._auto_refresh_tick, refresh_token)
        )
        self.refresh_token_timer.start()

    def _cancel_refresh_timer(self) -> None:
        timer, self.refresh_token_timer = self.refresh_token_timer, None
        if timer is not None:
            timer.cancel()


class SyncSupportedStorage(ABC):
    @abstractmethod
    def get_item(self, key: str) -> str | None: ...  # pragma: no cover

    @abstractmethod
    def set_item(self, key: str, value: str) -> None: ...  # pragma: no cover

    @abstractmethod
    def remove_item(self, key: str) -> None: ...  # pragma: no cover


class SyncMemoryStorage(SyncSupportedStorage):
    def __init__(self) -> None:
        self.storage: dict[str, str] = {}

    def get_item(self, key: str) -> str | None:
        if key in self.storage:
            return self.storage[key]
        return None

    def set_item(self, key: str, value: str) -> None:
        self.storage[key] = value

    def remove_item(self, key: str) -> None:
        if key in self.storage:
            del self.storage[key]


@dataclass
class _SyncSessionManager(_SessionManagerCommon[SyncHttpIO]):
    storage: SyncSupportedStorage
    refresh_token_timer: _SyncTimer | None = None
    _refresh_lock: threading.RLock = field(
        default_factory=threading.RLock, init=False, repr=False
    )
    """Held while a refresh runs, so threads refresh one at a time."""

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self._cancel_refresh_timer()

    def __enter__(self) -> Self:
        return self

    def load_session(self) -> Session | None:
        """
        Returns the stored session without refreshing it.

        A stored value that is not a valid session is removed, with a
        `SIGNED_OUT` notification.
        """
        raw_session = self.storage.get_item(self.storage_key)
        if not raw_session:
            self._current_session = None
            return None
        session = self.parse_valid_session(raw_session)
        if session is None:
            self._sign_out_locally(SignOutReason.SESSION_MISSING)
            return None
        self._current_session = session
        return session

    def get_session(self) -> Session | None:
        """
        Returns the session, refreshing it if necessary.

        The session returned can be null if the session is not detected which
        can happen in the event a user is not signed-in or has logged out.

        Concurrent calls share one refresh. A refresh the auth service rejects
        removes the session, notifies `SIGNED_OUT` and raises the error.
        """
        session = self.load_session()
        if session is None or not self._is_expiring(session):
            return session
        try:
            return self._single_flight(
                partial(self._refresh_stored_session, only_if_expiring=True)
            )
        except AuthSessionMissingError:
            return None

    def get_session_or_raise(self) -> Session:
        session = self.get_session()
        if not session:
            raise AuthSessionMissingError
        return session

    def refresh_session(self) -> Session:
        """Refresh the stored session whether or not it is expiring, after a
        refresh that is already running has finished. Raises
        `AuthSessionMissingError` when there is no stored session."""
        return self._single_flight(self._refresh_stored_session)

    def call_refresh_token(self, refresh_token: str) -> Session:
        """Refresh the session with `refresh_token`, after a refresh that is
        already running has finished."""
        return self._single_flight(partial(self._refresh_with, refresh_token))

    def save_session(self, session: Session) -> None:
        if session.expires_at is None:
            return
        self._current_session = session
        self.storage.set_item(self.storage_key, session.model_dump_json())
        self._schedule_refresh(
            self._refresh_delay(session.expires_at), session.refresh_token
        )

    def remove_session(self) -> None:
        self.storage.remove_item(self.storage_key)
        self._current_session = None
        self._cancel_refresh_timer()

    def recover_and_refresh(self) -> None:
        session = self.load_session()
        if session is None:
            return
        if not self._is_expiring(session):
            self.save_session(session)
            self.notify_all_subscribers(
                AuthStateChange(AuthChangeEvent.SIGNED_IN, session)
            )
            return
        if not session.refresh_token:
            self._sign_out_locally(SignOutReason.SESSION_MISSING)
            return
        if self.auto_refresh_token:
            self._refresh_or_retry()

    def _sign_out_locally(self, reason: SignOutReason) -> None:
        self.remove_session()
        self.notify_all_subscribers(self._signed_out(reason))

    def _single_flight(self, refresh: Callable[[], Session]) -> Session:
        """Run `refresh` once no other thread is refreshing. A refresh that
        reads the stored session first then finds the session the other
        thread saved and does not send a second request."""
        with self._refresh_lock:
            return refresh()

    def _refresh_stored_session(
        self, *, only_if_expiring: bool = False, scheduled_for: str | None = None
    ) -> Session:
        """Refresh the stored session with its own refresh token.

        The stored session is read again first, so a caller that waited for
        another refresh sees the session that refresh saved. It is returned
        as is when it is not expiring and `only_if_expiring` is set, or when
        its refresh token is no longer `scheduled_for`, the token the refresh
        was scheduled for.
        """
        session = self.load_session()
        if session is None:
            raise AuthSessionMissingError
        if not session.refresh_token:
            self._sign_out_locally(SignOutReason.SESSION_MISSING)
            raise AuthSessionMissingError
        if only_if_expiring and not self._is_expiring(session):
            return session
        if scheduled_for is not None and session.refresh_token != scheduled_for:
            return session
        return self._refresh_with(session.refresh_token)

    def _refresh_with(self, refresh_token: str) -> Session:
        if not refresh_token:
            raise AuthSessionMissingError
        try:
            session = self.refresh_access_token(refresh_token)
        except Exception as error:
            if _is_terminal_refresh_error(error):
                self._sign_out_locally(SignOutReason.SESSION_EXPIRED)
            raise
        self._failed_refreshes = 0
        self.save_session(session)
        self.notify_all_subscribers(
            AuthStateChange(AuthChangeEvent.TOKEN_REFRESHED, session)
        )
        return session

    def _auto_refresh_tick(self, refresh_token: str | None) -> None:
        # The timer that fired is spent, like in the async manager.
        self.refresh_token_timer = None
        self._refresh_or_retry(scheduled_for=refresh_token)

    def _refresh_or_retry(self, *, scheduled_for: str | None = None) -> None:
        try:
            self._single_flight(
                partial(self._refresh_stored_session, scheduled_for=scheduled_for)
            )
        except AuthSessionMissingError:
            return
        except Exception as error:
            delay = self._retry_in(error)
            if delay is not None:
                self._schedule_refresh(delay, None)

    def _schedule_refresh(self, seconds: float, refresh_token: str | None) -> None:
        """Refresh the stored session in `seconds`, unless its refresh token
        is no longer `refresh_token` by then. None refreshes it regardless."""
        self._cancel_refresh_timer()
        if seconds <= 0 or not self.auto_refresh_token:
            return
        self.refresh_token_timer = _SyncTimer(
            seconds, partial(self._auto_refresh_tick, refresh_token)
        )
        self.refresh_token_timer.start()

    def _cancel_refresh_timer(self) -> None:
        timer, self.refresh_token_timer = self.refresh_token_timer, None
        if timer is not None:
            timer.cancel()
