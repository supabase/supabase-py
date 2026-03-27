from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Generic

from supabase_utils.http.headers import Headers
from supabase_utils.http.io import (
    AsyncHttpIO,
    HttpIO,
    HttpMethod,
    SyncHttpIO,
    handle_http_io,
)
from supabase_utils.http.query import URLQuery
from supabase_utils.http.request import EmptyRequest, JSONRequest
from yarl import URL

from .constants import EXPIRY_MARGIN, MAX_RETRIES, RETRY_INTERVAL, STORAGE_KEY
from .errors import AuthRetryableError, AuthSessionMissingError
from .helpers import parse_auth_response, parse_user_response
from .timer import AsyncTimer, SyncTimer
from .types import AuthChangeEvent, AuthResponse, Session, Subscription, UserResponse


class AsyncSupportedStorage(ABC):
    @abstractmethod
    async def get_item(self, key: str) -> str | None: ...  # pragma: no cover

    @abstractmethod
    async def set_item(self, key: str, value: str) -> None: ...  # pragma: no cover

    @abstractmethod
    async def remove_item(self, key: str) -> None: ...  # pragma: no cover


class AsyncMemoryStorage(AsyncSupportedStorage):
    def __init__(self) -> None:
        self.storage: Dict[str, str] = {}

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
class SessionManagerCommon(Generic[HttpIO]):
    """
    Common methods shared between sync and async implementations
    of the session manager.
    """

    base_url: URL
    executor: HttpIO
    default_headers: Headers
    state_change_emitters: Dict[str, Subscription]
    storage_key: str = field(default=STORAGE_KEY, kw_only=True)
    persist_session: bool = field(default=True, kw_only=True)
    network_retries: int = field(default=0, kw_only=True)
    in_memory_session: Session | None = field(default=None, kw_only=True)
    auto_refresh_token: bool = field(default=True, kw_only=True)

    def _refresh_access_token(self, refresh_token: str) -> HttpMethod[AuthResponse]:
        response = yield JSONRequest(
            method="POST",
            path=["token"],
            query=URLQuery.from_mapping({"grant_type": "refresh_token"}),
            body={"refresh_token": refresh_token},
        )
        return parse_auth_response(response)

    @handle_http_io
    def refresh_access_token(self, refresh_token: str) -> HttpMethod[AuthResponse]:
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

    def notify_all_subscribers(
        self,
        event: AuthChangeEvent,
        session: Session | None,
    ) -> None:
        for subscription in self.state_change_emitters.values():
            subscription.callback(event, session)


@dataclass
class AsyncSessionManager(SessionManagerCommon[AsyncHttpIO]):
    storage: AsyncSupportedStorage
    refresh_token_timer: AsyncTimer | None = None

    async def remove_session(self) -> None:
        if self.persist_session:
            await self.storage.remove_item(self.storage_key)
        else:
            self.in_memory_session = None
        if self.refresh_token_timer:
            self.refresh_token_timer.cancel()
            self.refresh_token_timer = None

    async def call_refresh_token(self, refresh_token: str) -> Session:
        if not refresh_token:
            raise AuthSessionMissingError()
        response = await self.refresh_access_token(refresh_token)
        if not response.session:
            raise AuthSessionMissingError()
        await self.save_session(response.session)
        self.notify_all_subscribers("TOKEN_REFRESHED", response.session)
        return response.session

    async def get_session(self) -> Session | None:
        """
        Returns the session, refreshing it if necessary.

        The session returned can be null if the session is not detected which
        can happen in the event a user is not signed-in or has logged out.
        """
        current_session: Session | None = None
        if self.persist_session:
            maybe_session = await self.storage.get_item(self.storage_key)
            current_session = self.parse_valid_session(maybe_session)
            if not current_session:
                await self.remove_session()
        else:
            current_session = self.in_memory_session

        if not current_session:
            return None
        time_now = round(time.time())
        has_expired = (
            current_session.expires_at <= time_now + EXPIRY_MARGIN
            if current_session.expires_at
            else False
        )
        if not has_expired:
            return current_session
        return await self.call_refresh_token(current_session.refresh_token)

    async def get_session_or_raise(self) -> Session:
        session = await self.get_session()
        if not session:
            raise AuthSessionMissingError()
        return session

    async def save_session(self, session: Session) -> None:
        if not self.persist_session:
            self.in_memory_session = session
        expire_at = session.expires_at
        if expire_at:
            time_now = round(time.time())
            expire_in = expire_at - time_now
            refresh_duration_before_expires = (
                EXPIRY_MARGIN if expire_in > EXPIRY_MARGIN else 0.5
            )
            value = (expire_in - refresh_duration_before_expires) * 1000
            self.start_auto_refresh_token(value)
        if self.persist_session and session.expires_at:
            await self.storage.set_item(self.storage_key, session.model_dump_json())

    async def recover_and_refresh(self) -> None:
        raw_session = await self.storage.get_item(self.storage_key)
        current_session = self.parse_valid_session(raw_session)
        if not current_session:
            if raw_session:
                await self.remove_session()
            return
        time_now = round(time.time())
        expires_at = current_session.expires_at
        if expires_at and expires_at < time_now + EXPIRY_MARGIN:
            refresh_token = current_session.refresh_token
            if self.auto_refresh_token and refresh_token:
                self.network_retries += 1
                try:
                    await self.call_refresh_token(refresh_token)
                    self.network_retries = 0
                except Exception as e:
                    if (
                        isinstance(e, AuthRetryableError)
                        and self.network_retries < MAX_RETRIES
                    ):
                        if self.refresh_token_timer:
                            self.refresh_token_timer.cancel()
                        self.refresh_token_timer = AsyncTimer(
                            (RETRY_INTERVAL ** (2 * (self.network_retries - 1))),
                            self.recover_and_refresh,
                        )
                        self.refresh_token_timer.start()
                        return
            await self.remove_session()
            return
        if self.persist_session:
            await self.save_session(current_session)
        self.notify_all_subscribers("SIGNED_IN", current_session)

    async def refresh_token_function(self) -> None:
        self.network_retries += 1
        try:
            session = await self.get_session()
            if session:
                await self.call_refresh_token(session.refresh_token)
                self.network_retries = 0
        except Exception as e:
            if isinstance(e, AuthRetryableError) and self.network_retries < MAX_RETRIES:
                self.start_auto_refresh_token(
                    (RETRY_INTERVAL ** (2 * (self.network_retries - 1))),
                )

    def start_auto_refresh_token(self, value: float) -> None:
        if self.refresh_token_timer:
            self.refresh_token_timer.cancel()
            self.refresh_token_timer = None
        if value <= 0 or not self.auto_refresh_token:
            return

        self.refresh_token_timer = AsyncTimer(value, self.refresh_token_function)
        self.refresh_token_timer.start()


class SyncSupportedStorage(ABC):
    @abstractmethod
    def get_item(self, key: str) -> str | None: ...  # pragma: no cover

    @abstractmethod
    def set_item(self, key: str, value: str) -> None: ...  # pragma: no cover

    @abstractmethod
    def remove_item(self, key: str) -> None: ...  # pragma: no cover


class SyncMemoryStorage(SyncSupportedStorage):
    def __init__(self) -> None:
        self.storage: Dict[str, str] = {}

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
class SyncSessionManager(SessionManagerCommon[SyncHttpIO]):
    storage: SyncSupportedStorage
    refresh_token_timer: SyncTimer | None = None

    def remove_session(self) -> None:
        if self.persist_session:
            self.storage.remove_item(self.storage_key)
        else:
            self.in_memory_session = None
        if self.refresh_token_timer:
            self.refresh_token_timer.cancel()
            self.refresh_token_timer = None

    def call_refresh_token(self, refresh_token: str) -> Session:
        if not refresh_token:
            raise AuthSessionMissingError()
        response = self.refresh_access_token(refresh_token)
        if not response.session:
            raise AuthSessionMissingError()
        self.save_session(response.session)
        self.notify_all_subscribers("TOKEN_REFRESHED", response.session)
        return response.session

    def get_session(self) -> Session | None:
        """
        Returns the session, refreshing it if necessary.

        The session returned can be null if the session is not detected which
        can happen in the event a user is not signed-in or has logged out.
        """
        current_session: Session | None = None
        if self.persist_session:
            maybe_session = self.storage.get_item(self.storage_key)
            current_session = self.parse_valid_session(maybe_session)
            if not current_session:
                self.remove_session()
        else:
            current_session = self.in_memory_session

        if not current_session:
            return None
        time_now = round(time.time())
        has_expired = (
            current_session.expires_at <= time_now + EXPIRY_MARGIN
            if current_session.expires_at
            else False
        )
        if not has_expired:
            return current_session
        return self.call_refresh_token(current_session.refresh_token)

    def get_session_or_raise(self) -> Session:
        session = self.get_session()
        if not session:
            raise AuthSessionMissingError()
        return session

    def save_session(self, session: Session) -> None:
        if not self.persist_session:
            self.in_memory_session = session
        expire_at = session.expires_at
        if expire_at:
            time_now = round(time.time())
            expire_in = expire_at - time_now
            refresh_duration_before_expires = (
                EXPIRY_MARGIN if expire_in > EXPIRY_MARGIN else 0.5
            )
            value = (expire_in - refresh_duration_before_expires) * 1000
            self.start_auto_refresh_token(value)
        if self.persist_session and session.expires_at:
            self.storage.set_item(self.storage_key, session.model_dump_json())

    def refresh_token_function(self) -> None:
        self.network_retries += 1
        try:
            session = self.get_session()
            if session:
                self.call_refresh_token(session.refresh_token)
                self.network_retries = 0
        except Exception as e:
            if isinstance(e, AuthRetryableError) and self.network_retries < MAX_RETRIES:
                self.start_auto_refresh_token(
                    RETRY_INTERVAL ** (2 * (self.network_retries - 1))
                )

    def recover_and_refresh(self) -> None:
        raw_session = self.storage.get_item(self.storage_key)
        current_session = self.parse_valid_session(raw_session)
        if not current_session:
            if raw_session:
                self.remove_session()
            return
        time_now = round(time.time())
        expires_at = current_session.expires_at
        if expires_at and expires_at < time_now + EXPIRY_MARGIN:
            refresh_token = current_session.refresh_token
            if self.auto_refresh_token and refresh_token:
                self.network_retries += 1
                try:
                    self.call_refresh_token(refresh_token)
                    self.network_retries = 0
                except Exception as e:
                    if (
                        isinstance(e, AuthRetryableError)
                        and self.network_retries < MAX_RETRIES
                    ):
                        if self.refresh_token_timer:
                            self.refresh_token_timer.cancel()
                        self.refresh_token_timer = SyncTimer(
                            (RETRY_INTERVAL ** (2 * (self.network_retries - 1))),
                            self.recover_and_refresh,
                        )
                        self.refresh_token_timer.start()
                        return
            self.remove_session()
            return
        if self.persist_session:
            self.save_session(current_session)
        self.notify_all_subscribers("SIGNED_IN", current_session)

    def start_auto_refresh_token(self, value: float) -> None:
        if self.refresh_token_timer:
            self.refresh_token_timer.cancel()
            self.refresh_token_timer = None
        if value <= 0 or not self.auto_refresh_token:
            return

        self.refresh_token_timer = SyncTimer(value, self.refresh_token_function)
        self.refresh_token_timer.start()
