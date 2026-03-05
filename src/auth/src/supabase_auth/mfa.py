from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Literal

from httpx import Headers
from supabase_utils.http import (
    AsyncHttpIO,
    EmptyRequest,
    HttpIO,
    HttpMethod,
    JSONRequest,
    SyncHttpIO,
    handle_http_io,
)
from yarl import URL

from .errors import AuthSessionMissingError
from .helpers import (
    decode_jwt,
    validate_model,
)
from .session import AsyncSessionManager, SyncSessionManager
from .types import (
    AMREntry,
    AuthMFAChallengeResponse,
    AuthMFAEnrollResponse,
    AuthMFAGetAuthenticatorAssuranceLevelResponse,
    AuthMFAListFactorsResponse,
    AuthMFAUnenrollResponse,
    AuthMFAVerifyResponse,
    MFAEnrollParams,
    Session,
    UserResponse,
)


@dataclass
class SupabaseAuthMFAHttpClient(Generic[HttpIO]):
    """
    Contains the full multi-factor authentication API http calls
    """

    executor: HttpIO
    base_url: URL
    default_headers: Headers

    @handle_http_io
    def _enroll(
        self, session: Session, params: MFAEnrollParams
    ) -> HttpMethod[AuthMFAEnrollResponse]:
        response = yield JSONRequest(
            method="POST",
            path=["factors"],
            body=params,
            headers=session.encode_access_token(),
        )
        auth_response = validate_model(response, AuthMFAEnrollResponse)
        if params.factor_type == "totp" and auth_response.totp:
            auth_response.totp.qr_code = (
                f"data:image/svg+xml;utf-8,{auth_response.totp.qr_code}"
            )
        return auth_response

    def _challenge_http(
        self,
        session: Session,
        factor_id: str,
        channel: Literal["sms", "whatsapp"] | None = None,
    ) -> HttpMethod[AuthMFAChallengeResponse]:
        response = yield JSONRequest(
            method="POST",
            path=["factors", factor_id, "challenge"],
            body={"channel": channel},
            headers=session.encode_access_token(),
        )
        return validate_model(response, AuthMFAChallengeResponse)

    @handle_http_io
    def _challenge(
        self,
        session: Session,
        factor_id: str,
        channel: Literal["sms", "whatsapp"] | None = None,
    ) -> HttpMethod[AuthMFAChallengeResponse]:
        return self._challenge_http(session, factor_id, channel)

    def _verify_http(
        self, session: Session, factor_id: str, code: str, challenge_id: str
    ) -> HttpMethod[tuple[AuthMFAVerifyResponse, Session]]:
        response = yield JSONRequest(
            method="POST",
            path=["factors", factor_id, "verify"],
            body={
                "factor_id": factor_id,
                "code": code,
                "challenge_id": challenge_id,
            },
            headers=session.encode_access_token(),
        )
        auth_response = validate_model(response, AuthMFAVerifyResponse)
        session = validate_model(response, Session)
        return auth_response, session

    @handle_http_io
    def _verify(
        self, session: Session, factor_id: str, code: str, challenge_id: str
    ) -> HttpMethod[tuple[AuthMFAVerifyResponse, Session]]:
        return self._verify_http(session, factor_id, code, challenge_id)

    @handle_http_io
    def _challenge_and_verify(
        self,
        session: Session,
        factor_id: str,
        code: str,
    ) -> HttpMethod[tuple[AuthMFAVerifyResponse, Session]]:
        response = yield from self._challenge_http(session, factor_id)
        result = yield from self._verify_http(
            session, factor_id, code, challenge_id=response.id
        )
        return result

    @handle_http_io
    def _unenroll(
        self, session: Session, factor_id: str
    ) -> HttpMethod[AuthMFAUnenrollResponse]:
        response = yield EmptyRequest(
            method="DELETE",
            path=["factors", factor_id],
            headers=session.encode_access_token(),
        )
        return validate_model(response, AuthMFAUnenrollResponse)

    def _list_factors(
        self, user_response: UserResponse | None
    ) -> AuthMFAListFactorsResponse:
        factors = user_response.user.factors or [] if user_response else []
        totp = [
            f for f in factors if f.factor_type == "totp" and f.status == "verified"
        ]
        phone = [
            f for f in factors if f.factor_type == "phone" and f.status == "verified"
        ]
        return AuthMFAListFactorsResponse(all=factors, totp=totp, phone=phone)

    def _get_authenticator_assurance_level(
        self,
        session: Session | None = None,
    ) -> AuthMFAGetAuthenticatorAssuranceLevelResponse:
        if not session:
            return AuthMFAGetAuthenticatorAssuranceLevelResponse(
                current_level=None,
                next_level=None,
                current_authentication_methods=[],
            )
        payload = decode_jwt(session.access_token).payload
        current_level = payload.aal
        verified_factors = [
            f for f in session.user.factors or [] if f.status == "verified"
        ]
        next_level = "aal2" if verified_factors else current_level
        amr_dict_list = payload.amr or []
        current_authentication_methods = [
            AMREntry.model_validate(amr) for amr in amr_dict_list
        ]
        return AuthMFAGetAuthenticatorAssuranceLevelResponse(
            current_level=current_level,
            next_level=next_level,
            current_authentication_methods=current_authentication_methods,
        )


@dataclass
class AsyncSupabaseAuthMFAClient(SupabaseAuthMFAHttpClient[AsyncHttpIO]):
    session_manager: AsyncSessionManager

    async def enroll(self, params: MFAEnrollParams) -> AuthMFAEnrollResponse:
        """
        Starts the enrollment process for a new Multi-Factor Authentication
        factor. This method creates a new factor in the 'unverified' state.
        Present the QR code or secret to the user and ask them to add it to their
        authenticator app. Ask the user to provide you with an authenticator code
        from their app and verify it by calling challenge and then verify.

        The first successful verification of an unverified factor activates the
        factor. All other sessions are logged out and the current one gets an
        `aal2` authenticator level.
        """
        session = await self.session_manager.get_session()
        if not session:
            raise AuthSessionMissingError()
        return await self._enroll(session, params)

    async def challenge(
        self, factor_id: str, channel: Literal["sms", "whatsapp"] | None = None
    ) -> AuthMFAChallengeResponse:
        """
        Prepares a challenge used to verify that a user has access to a MFA
        factor. Provide the challenge ID and verification code by calling `verify`.
        """
        session = await self.session_manager.get_session()
        if not session:
            raise AuthSessionMissingError()
        return await self._challenge(session, factor_id, channel)

    async def challenge_and_verify(
        self,
        factor_id: str,
        code: str,
    ) -> AuthMFAVerifyResponse:
        """
        Helper method which creates a challenge and immediately uses the given code
        to verify against it thereafter. The verification code is provided by the
        user by entering a code seen in their authenticator app.
        """
        session = await self.session_manager.get_session()
        if not session:
            raise AuthSessionMissingError()
        response, session = await self._challenge_and_verify(session, factor_id, code)
        await self.session_manager.save_session(session)
        self.session_manager.notify_all_subscribers("TOKEN_REFRESHED", session)
        return response

    async def verify(
        self, factor_id: str, code: str, challenge_id: str
    ) -> AuthMFAVerifyResponse:
        """
        Verifies a verification code against a challenge. The verification code is
        provided by the user by entering a code seen in their authenticator app.
        """
        session = await self.session_manager.get_session()
        if not session:
            raise AuthSessionMissingError()
        response, session = await self._verify(session, factor_id, code, challenge_id)
        await self.session_manager.save_session(session)
        self.session_manager.notify_all_subscribers("MFA_CHALLENGE_VERIFIED", session)
        return response

    async def unenroll(self, factor_id: str) -> AuthMFAUnenrollResponse:
        """
        Unenroll removes a MFA factor. Unverified factors can safely be ignored
        and it's not necessary to unenroll them. Unenrolling a verified MFA factor
        cannot be done from a session with an `aal1` authenticator level.
        """
        session = await self.session_manager.get_session()
        if not session:
            raise AuthSessionMissingError()
        return await self._unenroll(session, factor_id)

    async def list_factors(self) -> AuthMFAListFactorsResponse:
        """
        Returns the list of MFA factors enabled for this user. For most use cases
        you should consider using `get_authenticator_assurance_level`.

        This uses a cached version of the factors and avoids incurring a network call.
        If you need to update this list, call `get_user` first.
        """
        session = await self.session_manager.get_session()
        if not session:
            raise AuthSessionMissingError()
        user = await self.session_manager.get_user(session.access_token)
        return self._list_factors(user)

    async def get_authenticator_assurance_level(
        self,
    ) -> AuthMFAGetAuthenticatorAssuranceLevelResponse:
        """
        Returns the Authenticator Assurance Level (AAL) for the active session.

        - `aal1` (or `null`) means that the user's identity has been verified only
        with a conventional login (email+password, OTP, magic link, social login,
        etc.).
        - `aal2` means that the user's identity has been verified both with a
        conventional login and at least one MFA factor.

        Although this method returns a promise, it's fairly quick (microseconds)
        and rarely uses the network. You can use this to check whether the current
        user needs to be shown a screen to verify their MFA factors.
        """
        session = await self.session_manager.get_session()
        return self._get_authenticator_assurance_level(session)


@dataclass
class SyncSupabaseAuthMFAClient(SupabaseAuthMFAHttpClient[SyncHttpIO]):
    session_manager: SyncSessionManager

    def enroll(self, params: MFAEnrollParams) -> AuthMFAEnrollResponse:
        """
        Starts the enrollment process for a new Multi-Factor Authentication
        factor. This method creates a new factor in the 'unverified' state.
        Present the QR code or secret to the user and ask them to add it to their
        authenticator app. Ask the user to provide you with an authenticator code
        from their app and verify it by calling challenge and then verify.

        The first successful verification of an unverified factor activates the
        factor. All other sessions are logged out and the current one gets an
        `aal2` authenticator level.
        """
        session = self.session_manager.get_session()
        if not session:
            raise AuthSessionMissingError()
        return self._enroll(session, params)

    def challenge(
        self, factor_id: str, channel: Literal["sms", "whatsapp"] | None = None
    ) -> AuthMFAChallengeResponse:
        """
        Prepares a challenge used to verify that a user has access to a MFA
        factor. Provide the challenge ID and verification code by calling `verify`.
        """
        session = self.session_manager.get_session()
        if not session:
            raise AuthSessionMissingError()
        return self._challenge(session, factor_id, channel)

    def challenge_and_verify(
        self,
        factor_id: str,
        code: str,
    ) -> AuthMFAVerifyResponse:
        """
        Helper method which creates a challenge and immediately uses the given code
        to verify against it thereafter. The verification code is provided by the
        user by entering a code seen in their authenticator app.
        """
        session = self.session_manager.get_session()
        if not session:
            raise AuthSessionMissingError()
        response, session = self._challenge_and_verify(session, factor_id, code)
        self.session_manager.save_session(session)
        self.session_manager.notify_all_subscribers("TOKEN_REFRESHED", session)
        return response

    def verify(
        self, factor_id: str, code: str, challenge_id: str
    ) -> AuthMFAVerifyResponse:
        """
        Verifies a verification code against a challenge. The verification code is
        provided by the user by entering a code seen in their authenticator app.
        """
        session = self.session_manager.get_session()
        if not session:
            raise AuthSessionMissingError()
        response, session = self._verify(session, factor_id, code, challenge_id)
        self.session_manager.save_session(session)
        self.session_manager.notify_all_subscribers("MFA_CHALLENGE_VERIFIED", session)
        return response

    def unenroll(self, factor_id: str) -> AuthMFAUnenrollResponse:
        """
        Unenroll removes a MFA factor. Unverified factors can safely be ignored
        and it's not necessary to unenroll them. Unenrolling a verified MFA factor
        cannot be done from a session with an `aal1` authenticator level.
        """
        session = self.session_manager.get_session()
        if not session:
            raise AuthSessionMissingError()
        return self._unenroll(session, factor_id)

    def list_factors(self) -> AuthMFAListFactorsResponse:
        """
        Returns the list of MFA factors enabled for this user. For most use cases
        you should consider using `get_authenticator_assurance_level`.

        This uses a cached version of the factors and avoids incurring a network call.
        If you need to update this list, call `get_user` first.
        """
        session = self.session_manager.get_session()
        if not session:
            raise AuthSessionMissingError()
        user = self.session_manager.get_user(session.access_token)
        return self._list_factors(user)

    def get_authenticator_assurance_level(
        self,
    ) -> AuthMFAGetAuthenticatorAssuranceLevelResponse:
        """
        Returns the Authenticator Assurance Level (AAL) for the active session.

        - `aal1` (or `null`) means that the user's identity has been verified only
        with a conventional login (email+password, OTP, magic link, social login,
        etc.).
        - `aal2` means that the user's identity has been verified both with a
        conventional login and at least one MFA factor.

        Although this method returns a promise, it's fairly quick (microseconds)
        and rarely uses the network. You can use this to check whether the current
        user needs to be shown a screen to verify their MFA factors.
        """
        session = self.session_manager.get_session()
        if not session:
            raise AuthSessionMissingError()
        return self._get_authenticator_assurance_level(session)
