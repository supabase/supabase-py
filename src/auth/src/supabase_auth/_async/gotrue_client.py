from __future__ import annotations

import time
from contextlib import suppress
from functools import partial
from json import loads
from typing import Callable, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlencode, urlparse
from uuid import uuid4

from jwt import get_algorithm_by_name

from ..constants import (
    DEFAULT_HEADERS,
    EXPIRY_MARGIN,
    GOTRUE_URL,
    MAX_RETRIES,
    RETRY_INTERVAL,
    STORAGE_KEY,
)
from ..errors import (
    AuthApiError,
    AuthImplicitGrantRedirectError,
    AuthInvalidCredentialsError,
    AuthInvalidJwtError,
    AuthRetryableError,
    AuthSessionMissingError,
)
from ..helpers import (
    decode_jwt,
    generate_pkce_challenge,
    generate_pkce_verifier,
    model_dump,
    model_dump_json,
    model_validate,
    parse_auth_otp_response,
    parse_auth_response,
    parse_jwks,
    parse_link_identity_response,
    parse_sso_response,
    parse_user_response,
    validate_exp,
)
from ..http_clients import AsyncClient
from ..timer import Timer
from ..types import (
    JWK,
    AuthChangeEvent,
    AuthenticatorAssuranceLevels,
    AuthFlowType,
    AuthMFAChallengeResponse,
    AuthMFAEnrollResponse,
    AuthMFAGetAuthenticatorAssuranceLevelResponse,
    AuthMFAListFactorsResponse,
    AuthMFAUnenrollResponse,
    AuthMFAVerifyResponse,
    AuthOtpResponse,
    AuthResponse,
    ClaimsResponse,
    CodeExchangeParams,
    IdentitiesResponse,
    JWKSet,
    MFAChallengeAndVerifyParams,
    MFAChallengeParams,
    MFAEnrollParams,
    MFAUnenrollParams,
    MFAVerifyParams,
    OAuthResponse,
    Options,
    Provider,
    ResendCredentials,
    Session,
    SignInAnonymouslyCredentials,
    SignInWithIdTokenCredentials,
    SignInWithOAuthCredentials,
    SignInWithPasswordCredentials,
    SignInWithPasswordlessCredentials,
    SignInWithSSOCredentials,
    SignOutOptions,
    SignUpWithPasswordCredentials,
    Subscription,
    UpdateUserOptions,
    UserAttributes,
    UserIdentity,
    UserResponse,
    VerifyOtpParams,
)
from .gotrue_admin_api import AsyncGoTrueAdminAPI
from .gotrue_base_api import AsyncGoTrueBaseAPI
from .gotrue_mfa_api import AsyncGoTrueMFAAPI
from .storage import AsyncMemoryStorage, AsyncSupportedStorage


class AsyncGoTrueClient(AsyncGoTrueBaseAPI):
    def __init__(
        self,
        *,
        url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        storage_key: Optional[str] = None,
        auto_refresh_token: bool = True,
        persist_session: bool = True,
        storage: Optional[AsyncSupportedStorage] = None,
        http_client: Optional[AsyncClient] = None,
        flow_type: AuthFlowType = "implicit",
        verify: bool = True,
        proxy: Optional[str] = None,
    ) -> None:
        AsyncGoTrueBaseAPI.__init__(
            self,
            url=url or GOTRUE_URL,
            headers=headers or DEFAULT_HEADERS,
            http_client=http_client,
            verify=verify,
            proxy=proxy,
        )

        self._jwks: JWKSet = {"keys": []}
        self._jwks_ttl: float = 600  # 10 minutes
        self._jwks_cached_at: Optional[float] = None

        self._storage_key = storage_key or STORAGE_KEY
        self._auto_refresh_token = auto_refresh_token
        self._persist_session = persist_session
        self._storage = storage or AsyncMemoryStorage()
        self._in_memory_session: Optional[Session] = None
        self._refresh_token_timer: Optional[Timer] = None
        self._network_retries = 0
        self._state_change_emitters: Dict[str, Subscription] = {}
        self._flow_type = flow_type

        self.admin = AsyncGoTrueAdminAPI(
            url=self._url,
            headers=self._headers,
            http_client=self._http_client,
        )
        self.mfa = AsyncGoTrueMFAAPI()
        self.mfa.challenge = self._challenge
        self.mfa.challenge_and_verify = self._challenge_and_verify
        self.mfa.enroll = self._enroll
        self.mfa.get_authenticator_assurance_level = (
            self._get_authenticator_assurance_level
        )
        self.mfa.list_factors = self._list_factors
        self.mfa.unenroll = self._unenroll
        self.mfa.verify = self._verify

    # Initializations

    async def initialize(self, *, url: Optional[str] = None) -> None:
        if url and self._is_implicit_grant_flow(url):
            await self.initialize_from_url(url)
        else:
            await self.initialize_from_storage()

    async def initialize_from_storage(self) -> None:
        return await self._recover_and_refresh()

    async def initialize_from_url(self, url: str) -> None:
        try:
            if self._is_implicit_grant_flow(url):
                session, redirect_type = await self._get_session_from_url(url)
                await self._save_session(session)
                self._notify_all_subscribers("SIGNED_IN", session)
                if redirect_type == "recovery":
                    self._notify_all_subscribers("PASSWORD_RECOVERY", session)
        except Exception as e:
            await self._remove_session()
            raise e

    # Public methods

    async def sign_in_anonymously(
        self, credentials: Optional[SignInAnonymouslyCredentials] = None
    ) -> AuthResponse:
        """
        Creates a new anonymous user.
        """
        await self._remove_session()
        if credentials is None:
            credentials = {"options": {}}
        options = credentials.get("options", {})
        data = options.get("data") or {}
        captcha_token = options.get("captcha_token")
        response = await self._request(
            "POST",
            "signup",
            body={
                "data": data,
                "gotrue_meta_security": {
                    "captcha_token": captcha_token,
                },
            },
            xform=parse_auth_response,
        )
        if response.session:
            await self._save_session(response.session)
            self._notify_all_subscribers("SIGNED_IN", response.session)
        return response

    async def sign_up(
        self,
        credentials: SignUpWithPasswordCredentials,
    ) -> AuthResponse:
        """
        Creates a new user.
        """
        await self._remove_session()
        email = credentials.get("email")
        phone = credentials.get("phone")
        password = credentials.get("password")
        options = credentials.get("options", {})
        redirect_to = options.get("redirect_to") or options.get("email_redirect_to")
        data = options.get("data") or {}
        channel = options.get("channel", "sms")
        captcha_token = options.get("captcha_token")
        if email:
            response = await self._request(
                "POST",
                "signup",
                body={
                    "email": email,
                    "password": password,
                    "data": data,
                    "gotrue_meta_security": {
                        "captcha_token": captcha_token,
                    },
                },
                redirect_to=redirect_to,
                xform=parse_auth_response,
            )
        elif phone:
            response = await self._request(
                "POST",
                "signup",
                body={
                    "phone": phone,
                    "password": password,
                    "data": data,
                    "channel": channel,
                    "gotrue_meta_security": {
                        "captcha_token": captcha_token,
                    },
                },
                xform=parse_auth_response,
            )
        else:
            raise AuthInvalidCredentialsError(
                "You must provide either an email or phone number and a password"
            )
        if response.session:
            await self._save_session(response.session)
            self._notify_all_subscribers("SIGNED_IN", response.session)
        return response

    async def sign_in_with_password(
        self,
        credentials: SignInWithPasswordCredentials,
    ) -> AuthResponse:
        """
        Log in an existing user with an email or phone and password.
        """
        await self._remove_session()
        email = credentials.get("email")
        phone = credentials.get("phone")
        password = credentials.get("password")
        options = credentials.get("options", {})
        data = options.get("data") or {}
        captcha_token = options.get("captcha_token")
        if email:
            response = await self._request(
                "POST",
                "token",
                body={
                    "email": email,
                    "password": password,
                    "data": data,
                    "gotrue_meta_security": {
                        "captcha_token": captcha_token,
                    },
                },
                query={
                    "grant_type": "password",
                },
                xform=parse_auth_response,
            )
        elif phone:
            response = await self._request(
                "POST",
                "token",
                body={
                    "phone": phone,
                    "password": password,
                    "data": data,
                    "gotrue_meta_security": {
                        "captcha_token": captcha_token,
                    },
                },
                query={
                    "grant_type": "password",
                },
                xform=parse_auth_response,
            )
        else:
            raise AuthInvalidCredentialsError(
                "You must provide either an email or phone number and a password"
            )
        if response.session:
            await self._save_session(response.session)
            self._notify_all_subscribers("SIGNED_IN", response.session)
        return response

    async def sign_in_with_id_token(
        self,
        credentials: SignInWithIdTokenCredentials,
    ) -> AuthResponse:
        """
        Allows signing in with an OIDC ID token. The authentication provider used should be enabled and configured.
        """
        await self._remove_session()
        provider = credentials.get("provider")
        token = credentials.get("token")
        access_token = credentials.get("access_token")
        nonce = credentials.get("nonce")
        options = credentials.get("options", {})
        captcha_token = options.get("captcha_token")

        response = await self._request(
            "POST",
            "token",
            body={
                "provider": provider,
                "id_token": token,
                "access_token": access_token,
                "nonce": nonce,
                "gotrue_meta_security": {
                    "captcha_token": captcha_token,
                },
            },
            query={
                "grant_type": "id_token",
            },
            xform=parse_auth_response,
        )

        if response.session:
            await self._save_session(response.session)
            self._notify_all_subscribers("SIGNED_IN", response.session)
        return response

    async def sign_in_with_sso(self, credentials: SignInWithSSOCredentials):
        """
        Attempts a single-sign on using an enterprise Identity Provider. A
        successful SSO attempt will redirect the current page to the identity
        provider authorization page. The redirect URL is implementation and SSO
        protocol specific.

        You can use it by providing a SSO domain. Typically you can extract this
        domain by asking users for their email address. If this domain is
        registered on the Auth instance the redirect will use that organization's
        currently active SSO Identity Provider for the login.
        If you have built an organization-specific login page, you can use the
        organization's SSO Identity Provider UUID directly instead.
        """
        await self._remove_session()
        provider_id = credentials.get("provider_id")
        domain = credentials.get("domain")
        options = credentials.get("options", {})
        redirect_to = options.get("redirect_to")
        captcha_token = options.get("captcha_token")
        # HTTPX currently does not follow redirects: https://www.python-httpx.org/compatibility/
        # Additionally, unlike the JS client, Python is a server side language and it's not possible
        # to automatically redirect in browser for hte user
        skip_http_redirect = options.get("skip_http_redirect", True)

        if domain:
            return await self._request(
                "POST",
                "sso",
                body={
                    "domain": domain,
                    "skip_http_redirect": skip_http_redirect,
                    "gotrue_meta_security": {
                        "captcha_token": captcha_token,
                    },
                    "redirect_to": redirect_to,
                },
                xform=parse_sso_response,
            )
        if provider_id:
            return await self._request(
                "POST",
                "sso",
                body={
                    "provider_id": provider_id,
                    "skip_http_redirect": skip_http_redirect,
                    "gotrue_meta_security": {
                        "captcha_token": captcha_token,
                    },
                    "redirect_to": redirect_to,
                },
                xform=parse_sso_response,
            )
        raise AuthInvalidCredentialsError(
            "You must provide either a domain or provider_id"
        )

    async def sign_in_with_oauth(
        self,
        credentials: SignInWithOAuthCredentials,
    ) -> OAuthResponse:
        """
        Log in an existing user via a third-party provider.
        """
        await self._remove_session()

        provider = credentials.get("provider")
        options = credentials.get("options", {})
        redirect_to = options.get("redirect_to")
        scopes = options.get("scopes")
        params = options.get("query_params", {})
        if redirect_to:
            params["redirect_to"] = redirect_to
        if scopes:
            params["scopes"] = scopes
        url_with_qs, _ = await self._get_url_for_provider(
            f"{self._url}/authorize", provider, params
        )
        return OAuthResponse(provider=provider, url=url_with_qs)

    async def link_identity(
        self, credentials: SignInWithOAuthCredentials
    ) -> OAuthResponse:
        provider = credentials.get("provider")
        options = credentials.get("options", {})
        redirect_to = options.get("redirect_to")
        scopes = options.get("scopes")
        params = options.get("query_params", {})
        if redirect_to:
            params["redirect_to"] = redirect_to
        if scopes:
            params["scopes"] = scopes
        params["skip_http_redirect"] = "true"
        url = "user/identities/authorize"
        _, query = await self._get_url_for_provider(url, provider, params)

        session = await self.get_session()
        if not session:
            raise AuthSessionMissingError()

        response = await self._request(
            method="GET",
            path=url,
            query=query,
            jwt=session.access_token,
            xform=parse_link_identity_response,
        )
        return OAuthResponse(provider=provider, url=response.url)

    async def get_user_identities(self):
        response = await self.get_user()
        return (
            IdentitiesResponse(identities=response.user.identities)
            if response.user
            else AuthSessionMissingError()
        )

    async def unlink_identity(self, identity: UserIdentity):
        session = await self.get_session()
        if not session:
            raise AuthSessionMissingError()

        return await self._request(
            "DELETE",
            f"user/identities/{identity.identity_id}",
            jwt=session.access_token,
        )

    async def sign_in_with_otp(
        self,
        credentials: SignInWithPasswordlessCredentials,
    ) -> AuthOtpResponse:
        """
        Log in a user using magiclink or a one-time password (OTP).

        If the `{{ .ConfirmationURL }}` variable is specified in
        the email template, a magiclink will be sent.

        If the `{{ .Token }}` variable is specified in the email
        template, an OTP will be sent.

        If you're using phone sign-ins, only an OTP will be sent.
        You won't be able to send a magiclink for phone sign-ins.
        """
        await self._remove_session()
        email = credentials.get("email")
        phone = credentials.get("phone")
        options = credentials.get("options", {})
        email_redirect_to = options.get("email_redirect_to")
        should_create_user = options.get("should_create_user", True)
        data = options.get("data")
        channel = options.get("channel", "sms")
        captcha_token = options.get("captcha_token")
        if email:
            return await self._request(
                "POST",
                "otp",
                body={
                    "email": email,
                    "data": data,
                    "create_user": should_create_user,
                    "gotrue_meta_security": {
                        "captcha_token": captcha_token,
                    },
                },
                redirect_to=email_redirect_to,
                xform=parse_auth_otp_response,
            )
        if phone:
            return await self._request(
                "POST",
                "otp",
                body={
                    "phone": phone,
                    "data": data,
                    "create_user": should_create_user,
                    "channel": channel,
                    "gotrue_meta_security": {
                        "captcha_token": captcha_token,
                    },
                },
                xform=parse_auth_otp_response,
            )
        raise AuthInvalidCredentialsError(
            "You must provide either an email or phone number"
        )

    async def resend(
        self,
        credentials: ResendCredentials,
    ) -> AuthOtpResponse:
        """
        Resends an existing signup confirmation email, email change email, SMS OTP or phone change OTP.
        """
        email = credentials.get("email")
        phone = credentials.get("phone")
        type = credentials.get("type")
        options = credentials.get("options", {})
        email_redirect_to = options.get("email_redirect_to")
        captcha_token = options.get("captcha_token")
        body = {
            "type": type,
            "gotrue_meta_security": {
                "captcha_token": captcha_token,
            },
        }

        if email is None and phone is None:
            raise AuthInvalidCredentialsError(
                "You must provide either an email or phone number"
            )

        body.update({"email": email} if email else {"phone": phone})

        return await self._request(
            "POST",
            "resend",
            body=body,
            redirect_to=email_redirect_to if email else None,
            xform=parse_auth_otp_response,
        )

    async def verify_otp(self, params: VerifyOtpParams) -> AuthResponse:
        """
        Log in a user given a User supplied OTP received via mobile.
        """
        await self._remove_session()
        response = await self._request(
            "POST",
            "verify",
            body={
                "gotrue_meta_security": {
                    "captcha_token": params.get("options", {}).get("captcha_token"),
                },
                **params,
            },
            redirect_to=params.get("options", {}).get("redirect_to"),
            xform=parse_auth_response,
        )
        if response.session:
            await self._save_session(response.session)
            self._notify_all_subscribers("SIGNED_IN", response.session)
        return response

    async def reauthenticate(self) -> AuthResponse:
        session = await self.get_session()
        if not session:
            raise AuthSessionMissingError()

        return await self._request(
            "GET",
            "reauthenticate",
            jwt=session.access_token,
            xform=parse_auth_response,
        )

    async def get_session(self) -> Optional[Session]:
        """
        Returns the session, refreshing it if necessary.

        The session returned can be null if the session is not detected which
        can happen in the event a user is not signed-in or has logged out.
        """
        current_session: Optional[Session] = None
        if self._persist_session:
            maybe_session = await self._storage.get_item(self._storage_key)
            current_session = self._get_valid_session(maybe_session)
            if not current_session:
                await self._remove_session()
        else:
            current_session = self._in_memory_session
        if not current_session:
            return None
        time_now = round(time.time())
        has_expired = (
            current_session.expires_at <= time_now + EXPIRY_MARGIN
            if current_session.expires_at
            else False
        )
        return (
            await self._call_refresh_token(current_session.refresh_token)
            if has_expired
            else current_session
        )

    async def get_user(self, jwt: Optional[str] = None) -> Optional[UserResponse]:
        """
        Gets the current user details if there is an existing session.

        Takes in an optional access token `jwt`. If no `jwt` is provided,
        `get_user()` will attempt to get the `jwt` from the current session.
        """
        if not jwt:
            session = await self.get_session()
            if session:
                jwt = session.access_token
            else:
                return None
        return await self._request("GET", "user", jwt=jwt, xform=parse_user_response)

    async def update_user(
        self, attributes: UserAttributes, options: UpdateUserOptions = {}
    ) -> UserResponse:
        """
        Updates user data, if there is a logged in user.
        """
        session = await self.get_session()
        if not session:
            raise AuthSessionMissingError()
        response = await self._request(
            "PUT",
            "user",
            body=attributes,
            redirect_to=options.get("email_redirect_to"),
            jwt=session.access_token,
            xform=parse_user_response,
        )
        session.user = response.user
        await self._save_session(session)
        self._notify_all_subscribers("USER_UPDATED", session)
        return response

    async def set_session(self, access_token: str, refresh_token: str) -> AuthResponse:
        """
        Sets the session data from the current session. If the current session
        is expired, `set_session` will take care of refreshing it to obtain a
        new session.

        If the refresh token in the current session is invalid and the current
        session has expired, an error will be thrown.

        If the current session does not contain at `expires_at` field,
        `set_session` will use the exp claim defined in the access token.

        The current session that minimally contains an access token,
        refresh token and a user.
        """
        time_now = round(time.time())
        expires_at = time_now
        has_expired = True
        session: Optional[Session] = None
        if access_token and access_token.split(".")[1]:
            payload = decode_jwt(access_token)["payload"]
            exp = payload.get("exp")
            if exp:
                expires_at = int(exp)
                has_expired = expires_at <= time_now
        if has_expired:
            if not refresh_token:
                raise AuthSessionMissingError()
            response = await self._refresh_access_token(refresh_token)
            if not response.session:
                return AuthResponse()
            session = response.session
        else:
            response = await self.get_user(access_token)
            session = Session(
                access_token=access_token,
                refresh_token=refresh_token,
                user=response.user,
                token_type="bearer",
                expires_in=expires_at - time_now,
                expires_at=expires_at,
            )
        await self._save_session(session)
        self._notify_all_subscribers("TOKEN_REFRESHED", session)
        return AuthResponse(session=session, user=response.user)

    async def refresh_session(
        self, refresh_token: Optional[str] = None
    ) -> AuthResponse:
        """
        Returns a new session, regardless of expiry status.

        Takes in an optional current session. If not passed in, then refreshSession()
        will attempt to retrieve it from getSession(). If the current session's
        refresh token is invalid, an error will be thrown.
        """
        if not refresh_token:
            session = await self.get_session()
            if session:
                refresh_token = session.refresh_token
        if not refresh_token:
            raise AuthSessionMissingError()
        session = await self._call_refresh_token(refresh_token)
        return AuthResponse(session=session, user=session.user)

    async def sign_out(self, options: SignOutOptions = {"scope": "global"}) -> None:
        """
        `sign_out` will remove the logged in user from the
        current session and log them out - removing all items from storage and then trigger a `"SIGNED_OUT"` event.

        For advanced use cases, you can revoke all refresh tokens for a user by passing a user's JWT through to `admin.sign_out`.

        There is no way to revoke a user's access token jwt until it expires.
        It is recommended to set a shorter expiry on the jwt for this reason.
        """
        with suppress(AuthApiError):
            session = await self.get_session()
            access_token = session.access_token if session else None
            if access_token:
                await self.admin.sign_out(access_token, options["scope"])

        if options["scope"] != "others":
            await self._remove_session()
            self._notify_all_subscribers("SIGNED_OUT", None)

    def on_auth_state_change(
        self,
        callback: Callable[[AuthChangeEvent, Optional[Session]], None],
    ) -> Subscription:
        """
        Receive a notification every time an auth event happens.
        """
        unique_id = str(uuid4())

        def _unsubscribe() -> None:
            self._state_change_emitters.pop(unique_id)

        subscription = Subscription(
            id=unique_id,
            callback=callback,
            unsubscribe=_unsubscribe,
        )
        self._state_change_emitters[unique_id] = subscription
        return subscription

    async def reset_password_for_email(self, email: str, options: Options = {}) -> None:
        """
        Sends a password reset request to an email address.
        """
        await self._request(
            "POST",
            "recover",
            body={
                "email": email,
                "gotrue_meta_security": {
                    "captcha_token": options.get("captcha_token"),
                },
            },
            redirect_to=options.get("redirect_to"),
        )

    async def reset_password_email(
        self,
        email: str,
        options: Options = {},
    ) -> None:
        """
        Sends a password reset request to an email address.
        """
        await self.reset_password_for_email(email, options)

    # MFA methods

    async def _enroll(self, params: MFAEnrollParams) -> AuthMFAEnrollResponse:
        session = await self.get_session()
        if not session:
            raise AuthSessionMissingError()

        body = {
            "friendly_name": params.get("friendly_name"),
            "factor_type": params.get("factor_type"),
        }

        if params["factor_type"] == "phone":
            body["phone"] = params.get("phone")
        else:
            body["issuer"] = params.get("issuer")

        response = await self._request(
            "POST",
            "factors",
            body=body,
            jwt=session.access_token,
            xform=partial(model_validate, AuthMFAEnrollResponse),
        )
        if params["factor_type"] == "totp" and response.totp.qr_code:
            response.totp.qr_code = f"data:image/svg+xml;utf-8,{response.totp.qr_code}"
        return response

    async def _challenge(self, params: MFAChallengeParams) -> AuthMFAChallengeResponse:
        session = await self.get_session()
        if not session:
            raise AuthSessionMissingError()
        return await self._request(
            "POST",
            f"factors/{params.get('factor_id')}/challenge",
            body={"channel": params.get("channel")},
            jwt=session.access_token,
            xform=partial(model_validate, AuthMFAChallengeResponse),
        )

    async def _challenge_and_verify(
        self,
        params: MFAChallengeAndVerifyParams,
    ) -> AuthMFAVerifyResponse:
        response = await self._challenge(
            {
                "factor_id": params.get("factor_id"),
            }
        )
        return await self._verify(
            {
                "factor_id": params.get("factor_id"),
                "challenge_id": response.id,
                "code": params.get("code"),
            }
        )

    async def _verify(self, params: MFAVerifyParams) -> AuthMFAVerifyResponse:
        session = await self.get_session()
        if not session:
            raise AuthSessionMissingError()
        response = await self._request(
            "POST",
            f"factors/{params.get('factor_id')}/verify",
            body=params,
            jwt=session.access_token,
            xform=partial(model_validate, AuthMFAVerifyResponse),
        )
        session = model_validate(Session, model_dump(response))
        await self._save_session(session)
        self._notify_all_subscribers("MFA_CHALLENGE_VERIFIED", session)
        return response

    async def _unenroll(self, params: MFAUnenrollParams) -> AuthMFAUnenrollResponse:
        session = await self.get_session()
        if not session:
            raise AuthSessionMissingError()
        return await self._request(
            "DELETE",
            f"factors/{params.get('factor_id')}",
            jwt=session.access_token,
            xform=partial(model_validate, AuthMFAUnenrollResponse),
        )

    async def _list_factors(self) -> AuthMFAListFactorsResponse:
        response = await self.get_user()
        all = response.user.factors or []
        totp = [f for f in all if f.factor_type == "totp" and f.status == "verified"]
        phone = [f for f in all if f.factor_type == "phone" and f.status == "verified"]
        return AuthMFAListFactorsResponse(all=all, totp=totp, phone=phone)

    async def _get_authenticator_assurance_level(
        self,
    ) -> AuthMFAGetAuthenticatorAssuranceLevelResponse:
        session = await self.get_session()
        if not session:
            return AuthMFAGetAuthenticatorAssuranceLevelResponse(
                current_level=None,
                next_level=None,
                current_authentication_methods=[],
            )
        payload = decode_jwt(session.access_token)["payload"]
        current_level: Optional[AuthenticatorAssuranceLevels] = None
        if payload.get("aal"):
            current_level = payload.get("aal")
        verified_factors = [
            f for f in session.user.factors or [] if f.status == "verified"
        ]
        next_level = "aal2" if verified_factors else current_level
        current_authentication_methods = payload.get("amr") or []
        return AuthMFAGetAuthenticatorAssuranceLevelResponse(
            current_level=current_level,
            next_level=next_level,
            current_authentication_methods=current_authentication_methods,
        )

    # Private methods

    async def _remove_session(self) -> None:
        if self._persist_session:
            await self._storage.remove_item(self._storage_key)
        else:
            self._in_memory_session = None
        if self._refresh_token_timer:
            self._refresh_token_timer.cancel()
            self._refresh_token_timer = None

    async def _get_session_from_url(
        self,
        url: str,
    ) -> Tuple[Session, Optional[str]]:
        if not self._is_implicit_grant_flow(url):
            raise AuthImplicitGrantRedirectError("Not a valid implicit grant flow url.")
        result = urlparse(url)
        params = parse_qs(result.query)
        error_description = self._get_param(params, "error_description")
        if error_description:
            error_code = self._get_param(params, "error_code")
            error = self._get_param(params, "error")
            if not error_code:
                raise AuthImplicitGrantRedirectError("No error_code detected.")
            if not error:
                raise AuthImplicitGrantRedirectError("No error detected.")
            raise AuthImplicitGrantRedirectError(
                error_description,
                {"code": error_code, "error": error},
            )
        provider_token = self._get_param(params, "provider_token")
        provider_refresh_token = self._get_param(params, "provider_refresh_token")
        access_token = self._get_param(params, "access_token")
        if not access_token:
            raise AuthImplicitGrantRedirectError("No access_token detected.")
        expires_in = self._get_param(params, "expires_in")
        if not expires_in:
            raise AuthImplicitGrantRedirectError("No expires_in detected.")
        refresh_token = self._get_param(params, "refresh_token")
        if not refresh_token:
            raise AuthImplicitGrantRedirectError("No refresh_token detected.")
        token_type = self._get_param(params, "token_type")
        if not token_type:
            raise AuthImplicitGrantRedirectError("No token_type detected.")
        time_now = round(time.time())
        expires_at = time_now + int(expires_in)
        user = await self.get_user(access_token)
        session = Session(
            provider_token=provider_token,
            provider_refresh_token=provider_refresh_token,
            access_token=access_token,
            expires_in=int(expires_in),
            expires_at=expires_at,
            refresh_token=refresh_token,
            token_type=token_type,
            user=user.user,
        )
        redirect_type = self._get_param(params, "type")
        return session, redirect_type

    async def _recover_and_refresh(self) -> None:
        raw_session = await self._storage.get_item(self._storage_key)
        current_session = self._get_valid_session(raw_session)
        if not current_session:
            if raw_session:
                await self._remove_session()
            return
        time_now = round(time.time())
        expires_at = current_session.expires_at
        if expires_at and expires_at < time_now + EXPIRY_MARGIN:
            refresh_token = current_session.refresh_token
            if self._auto_refresh_token and refresh_token:
                self._network_retries += 1
                try:
                    await self._call_refresh_token(refresh_token)
                    self._network_retries = 0
                except Exception as e:
                    if (
                        isinstance(e, AuthRetryableError)
                        and self._network_retries < MAX_RETRIES
                    ):
                        if self._refresh_token_timer:
                            self._refresh_token_timer.cancel()
                        self._refresh_token_timer = Timer(
                            (RETRY_INTERVAL ** (self._network_retries * 100)),
                            self._recover_and_refresh,
                        )
                        self._refresh_token_timer.start()
                        return
            await self._remove_session()
            return
        if self._persist_session:
            await self._save_session(current_session)
        self._notify_all_subscribers("SIGNED_IN", current_session)

    async def _call_refresh_token(self, refresh_token: str) -> Session:
        if not refresh_token:
            raise AuthSessionMissingError()
        response = await self._refresh_access_token(refresh_token)
        if not response.session:
            raise AuthSessionMissingError()
        await self._save_session(response.session)
        self._notify_all_subscribers("TOKEN_REFRESHED", response.session)
        return response.session

    async def _refresh_access_token(self, refresh_token: str) -> AuthResponse:
        return await self._request(
            "POST",
            "token",
            query={"grant_type": "refresh_token"},
            body={"refresh_token": refresh_token},
            xform=parse_auth_response,
        )

    async def _save_session(self, session: Session) -> None:
        if not self._persist_session:
            self._in_memory_session = session
        expire_at = session.expires_at
        if expire_at:
            time_now = round(time.time())
            expire_in = expire_at - time_now
            refresh_duration_before_expires = (
                EXPIRY_MARGIN if expire_in > EXPIRY_MARGIN else 0.5
            )
            value = (expire_in - refresh_duration_before_expires) * 1000
            await self._start_auto_refresh_token(value)
        if self._persist_session and session.expires_at:
            await self._storage.set_item(self._storage_key, model_dump_json(session))

    async def _start_auto_refresh_token(self, value: float) -> None:
        if self._refresh_token_timer:
            self._refresh_token_timer.cancel()
            self._refresh_token_timer = None
        if value <= 0 or not self._auto_refresh_token:
            return

        async def refresh_token_function():
            self._network_retries += 1
            try:
                session = await self.get_session()
                if session:
                    await self._call_refresh_token(session.refresh_token)
                    self._network_retries = 0
            except Exception as e:
                if (
                    isinstance(e, AuthRetryableError)
                    and self._network_retries < MAX_RETRIES
                ):
                    await self._start_auto_refresh_token(
                        RETRY_INTERVAL ** (self._network_retries * 100)
                    )

        self._refresh_token_timer = Timer(value, refresh_token_function)
        self._refresh_token_timer.start()

    def _notify_all_subscribers(
        self,
        event: AuthChangeEvent,
        session: Optional[Session],
    ) -> None:
        for subscription in self._state_change_emitters.values():
            subscription.callback(event, session)

    def _get_valid_session(
        self,
        raw_session: Optional[str],
    ) -> Optional[Session]:
        if not raw_session:
            return None
        data = loads(raw_session)
        if not data:
            return None
        if not data.get("access_token"):
            return None
        if not data.get("refresh_token"):
            return None
        if not data.get("expires_at"):
            return None
        try:
            expires_at = int(data["expires_at"])
            data["expires_at"] = expires_at
        except ValueError:
            return None
        try:
            return model_validate(Session, data)
        except Exception:
            return None

    def _get_param(
        self,
        query_params: Dict[str, List[str]],
        name: str,
    ) -> Optional[str]:
        return query_params[name][0] if name in query_params else None

    def _is_implicit_grant_flow(self, url: str) -> bool:
        result = urlparse(url)
        params = parse_qs(result.query)
        return "access_token" in params or "error_description" in params

    async def _get_url_for_provider(
        self,
        url: str,
        provider: Provider,
        params: Dict[str, str],
    ) -> Tuple[str, Dict[str, str]]:
        if self._flow_type == "pkce":
            code_verifier = generate_pkce_verifier()
            code_challenge = generate_pkce_challenge(code_verifier)
            await self._storage.set_item(
                f"{self._storage_key}-code-verifier", code_verifier
            )
            code_challenge_method = (
                "plain" if code_verifier == code_challenge else "s256"
            )
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = code_challenge_method

        params["provider"] = provider
        query = urlencode(params)
        return f"{url}?{query}", params

    async def exchange_code_for_session(self, params: CodeExchangeParams):
        code_verifier = params.get("code_verifier") or await self._storage.get_item(
            f"{self._storage_key}-code-verifier"
        )
        response = await self._request(
            "POST",
            "token",
            query={"grant_type": "pkce"},
            body={
                "auth_code": params.get("auth_code"),
                "code_verifier": code_verifier,
            },
            redirect_to=params.get("redirect_to"),
            xform=parse_auth_response,
        )
        await self._storage.remove_item(f"{self._storage_key}-code-verifier")
        if response.session:
            await self._save_session(response.session)
            self._notify_all_subscribers("SIGNED_IN", response.session)
        return response

    async def _fetch_jwks(self, kid: str, jwks: JWKSet) -> JWK:
        jwk: Optional[JWK] = None

        # try fetching from the suplied keys.
        jwk = next((jwk for jwk in jwks["keys"] if jwk["kid"] == kid), None)

        if jwk:
            return jwk

        if self._jwks and (
            self._jwks_cached_at and time.time() - self._jwks_cached_at < self._jwks_ttl
        ):
            # try fetching from the cache.
            jwk = next(
                (jwk for jwk in self._jwks["keys"] if jwk["kid"] == kid),
                None,
            )
            if jwk:
                return jwk

        # jwk isn't cached in memory so we need to fetch it from the well-known endpoint
        response = await self._request("GET", ".well-known/jwks.json", xform=parse_jwks)
        if response:
            self._jwks = response
            self._jwks_cached_at = time.time()

            # find the signing key
            jwk = next((jwk for jwk in response["keys"] if jwk["kid"] == kid), None)
            if not jwk:
                raise AuthInvalidJwtError("No matching signing key found in JWKS")

            return jwk

        raise AuthInvalidJwtError("JWT has no valid kid")

    async def get_claims(
        self, jwt: Optional[str] = None, jwks: Optional[JWKSet] = None
    ) -> Optional[ClaimsResponse]:
        token = jwt
        if not token:
            session = await self.get_session()
            if not session:
                return None

            token = session.access_token

        decoded_jwt = decode_jwt(token)

        payload, header, signature = (
            decoded_jwt["payload"],
            decoded_jwt["header"],
            decoded_jwt["signature"],
        )
        raw_header, raw_payload = (
            decoded_jwt["raw"]["header"],
            decoded_jwt["raw"]["payload"],
        )

        validate_exp(payload["exp"])

        # if symmetric algorithm, fallback to get_user
        if "kid" not in header or header["alg"] == "HS256":
            await self.get_user(token)
            return ClaimsResponse(claims=payload, headers=header, signature=signature)

        algorithm = get_algorithm_by_name(header["alg"])
        signing_key = algorithm.from_jwk(
            await self._fetch_jwks(header["kid"], jwks or {"keys": []})
        )

        # verify the signature
        is_valid = algorithm.verify(
            msg=f"{raw_header}.{raw_payload}".encode(), key=signing_key, sig=signature
        )

        if not is_valid:
            raise AuthInvalidJwtError("Invalid JWT signature")

        # If verification succeeds, decode and return claims
        return ClaimsResponse(claims=payload, headers=header, signature=signature)

    def __del__(self) -> None:
        """Clean up resources when the client is destroyed."""
        if self._refresh_token_timer:
            try:
                # Try to cancel the timer
                self._refresh_token_timer.cancel()
            except:
                # Ignore errors if event loop is closed or selector is not registered
                pass
            finally:
                # Always set to None to prevent further attempts
                self._refresh_token_timer = None
