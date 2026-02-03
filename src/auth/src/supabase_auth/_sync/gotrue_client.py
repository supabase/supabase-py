from __future__ import annotations

import platform
import sys
import time
from contextlib import suppress
from typing import Callable, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse
from uuid import uuid4
from warnings import warn

from httpx import Client, QueryParams, Response
from jwt import get_algorithm_by_name
from typing_extensions import cast

from ..constants import (
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
    UserDoesntExist,
)
from ..helpers import (
    decode_jwt,
    generate_pkce_challenge,
    generate_pkce_verifier,
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
from ..timer import Timer
from ..types import (
    JWK,
    AMREntry,
    AuthChangeEvent,
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
    SignInWithEmailAndPasswordlessCredentialsOptions,
    SignInWithIdTokenCredentials,
    SignInWithOAuthCredentials,
    SignInWithPasswordCredentials,
    SignInWithPasswordlessCredentials,
    SignInWithPhoneAndPasswordlessCredentialsOptions,
    SignInWithSSOCredentials,
    SignOutOptions,
    SignUpWithEmailAndPasswordCredentialsOptions,
    SignUpWithPasswordCredentials,
    SignUpWithPhoneAndPasswordCredentialsOptions,
    SSOResponse,
    Subscription,
    UpdateUserOptions,
    UserAttributes,
    UserIdentity,
    UserResponse,
    VerifyOtpParams,
)
from ..version import __version__
from .gotrue_admin_api import SyncGoTrueAdminAPI
from .gotrue_base_api import SyncGoTrueBaseAPI
from .gotrue_mfa_api import SyncGoTrueMFAAPI
from .storage import SyncMemoryStorage, SyncSupportedStorage


class SyncGoTrueClient(SyncGoTrueBaseAPI):
    def __init__(
        self,
        *,
        url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        storage_key: Optional[str] = None,
        auto_refresh_token: bool = True,
        persist_session: bool = True,
        storage: Optional[SyncSupportedStorage] = None,
        http_client: Optional[Client] = None,
        flow_type: AuthFlowType = "implicit",
        verify: bool = True,
        proxy: Optional[str] = None,
    ) -> None:
        extra_headers = {
            "X-Client-Info": f"supabase-py/supabase_auth v{__version__}",
            "X-Supabase-Client-Platform": platform.system(),
            "X-Supabase-Client-Platform-Version": platform.release(),
            "X-Supabase-Client-Runtime": "python",
            "X-Supabase-Client-Runtime-Version": platform.python_version(),
        }
        if headers:
            extra_headers.update(headers)

        if sys.version_info < (3, 10):
            warn(
                "Python versions below 3.10 are deprecated and will not be supported in future versions. Please upgrade to Python 3.10 or newer.",
                DeprecationWarning,
                stacklevel=2,
            )

        SyncGoTrueBaseAPI.__init__(
            self,
            url=url or GOTRUE_URL,
            headers=extra_headers,
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
        self._storage = storage or SyncMemoryStorage()
        self._in_memory_session: Optional[Session] = None
        self._refresh_token_timer: Optional[Timer] = None
        self._network_retries = 0
        self._state_change_emitters: Dict[str, Subscription] = {}
        self._flow_type = flow_type

        self.admin = SyncGoTrueAdminAPI(
            url=self._url,
            headers=self._headers,
            http_client=self._http_client,
        )
        # TODO(@o-santi): why is it like this?
        self.mfa = SyncGoTrueMFAAPI()
        self.mfa.challenge = self._challenge  # type: ignore
        self.mfa.challenge_and_verify = self._challenge_and_verify  # type: ignore
        self.mfa.enroll = self._enroll  # type: ignore
        self.mfa.get_authenticator_assurance_level = (  # type: ignore
            self._get_authenticator_assurance_level
        )
        self.mfa.list_factors = self._list_factors  # type: ignore
        self.mfa.unenroll = self._unenroll  # type: ignore
        self.mfa.verify = self._verify  # type: ignore

    # Initializations

    def initialize(self, *, url: Optional[str] = None) -> None:
        if url and self._is_implicit_grant_flow(url):
            self.initialize_from_url(url)
        else:
            self.initialize_from_storage()

    def initialize_from_storage(self) -> None:
        return self._recover_and_refresh()

    def initialize_from_url(self, url: str) -> None:
        try:
            if self._is_implicit_grant_flow(url):
                session, redirect_type = self._get_session_from_url(url)
                self._save_session(session)
                self._notify_all_subscribers("SIGNED_IN", session)
                if redirect_type == "recovery":
                    self._notify_all_subscribers("PASSWORD_RECOVERY", session)
        except Exception as e:
            self._remove_session()
            raise e

    # Public methods

    def sign_in_anonymously(
        self, credentials: Optional[SignInAnonymouslyCredentials] = None
    ) -> AuthResponse:
        """
        Creates a new anonymous user.
        """
        self._remove_session()
        if credentials is None:
            credentials = {"options": {}}
        options = credentials.get("options", {})
        data = options.get("data") or {}
        captcha_token = options.get("captcha_token")
        response = self._request(
            "POST",
            "signup",
            body={
                "data": data,
                "gotrue_meta_security": {
                    "captcha_token": captcha_token,
                },
            },
        )
        auth_response = parse_auth_response(response)
        if auth_response.session:
            self._save_session(auth_response.session)
            self._notify_all_subscribers("SIGNED_IN", auth_response.session)
        return auth_response

    def sign_up(
        self,
        credentials: SignUpWithPasswordCredentials,
    ) -> AuthResponse:
        """
        Creates a new user.
        """
        self._remove_session()
        email = credentials.get("email")
        phone = credentials.get("phone")
        password = credentials.get("password")
        # TODO(@o-santi): this is horrible, but it is the easiest way to satisfy mypy
        #                 it should have been a builder pattern instead, and with proper classes
        if email and password:
            email_options = cast(
                SignUpWithEmailAndPasswordCredentialsOptions,
                credentials.get("options", {}),
            )
            data = email_options.get("data") or {}
            channel = email_options.get("channel", "sms")
            captcha_token = email_options.get("captcha_token")
            redirect_to = email_options.get("email_redirect_to")
            response = self._request(
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
            )
        elif phone and password:
            phone_options = cast(
                SignUpWithPhoneAndPasswordCredentialsOptions,
                credentials.get("options", {}),
            )
            data = phone_options.get("data") or {}
            channel = phone_options.get("channel", "sms")
            captcha_token = phone_options.get("captcha_token")
            response = self._request(
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
            )
        else:
            raise AuthInvalidCredentialsError(
                "You must provide either an email or phone number and a password"
            )

        auth_response = parse_auth_response(response)
        if auth_response.session:
            self._save_session(auth_response.session)
            self._notify_all_subscribers("SIGNED_IN", auth_response.session)
        return auth_response

    def sign_in_with_password(
        self,
        credentials: SignInWithPasswordCredentials,
    ) -> AuthResponse:
        """
        Log in an existing user with an email or phone and password.
        """
        self._remove_session()
        email = credentials.get("email")
        phone = credentials.get("phone")
        password = credentials.get("password")
        options = credentials.get("options", {})
        data = options.get("data") or {}
        captcha_token = options.get("captcha_token")
        if email and password:
            response = self._request(
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
                query=QueryParams(grant_type="password"),
            )
        elif phone and password:
            response = self._request(
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
                query=QueryParams(grant_type="password"),
            )
        else:
            raise AuthInvalidCredentialsError(
                "You must provide either an email or phone number and a password"
            )
        auth_response = parse_auth_response(response)
        if auth_response.session:
            self._save_session(auth_response.session)
            self._notify_all_subscribers("SIGNED_IN", auth_response.session)
        return auth_response

    def sign_in_with_id_token(
        self,
        credentials: SignInWithIdTokenCredentials,
    ) -> AuthResponse:
        """
        Allows signing in with an OIDC ID token. The authentication provider used should be enabled and configured.
        """
        self._remove_session()
        provider = credentials["provider"]
        token = credentials["token"]
        access_token = credentials.get("access_token")
        nonce = credentials.get("nonce")
        options = credentials.get("options", {})
        captcha_token = options.get("captcha_token")

        response = self._request(
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
            query=QueryParams(grant_type="id_token"),
        )
        auth_response = parse_auth_response(response)
        if auth_response.session:
            self._save_session(auth_response.session)
            self._notify_all_subscribers("SIGNED_IN", auth_response.session)
        return auth_response

    def sign_in_with_sso(self, credentials: SignInWithSSOCredentials) -> SSOResponse:
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
        self._remove_session()
        provider_id = credentials.get("provider_id")
        domain = credentials.get("domain")
        options = credentials.get("options", {})
        redirect_to = options.get("redirect_to")
        captcha_token = options.get("captcha_token")
        # HTTPX currently does not follow redirects: https://www.python-httpx.org/compatibility/
        # Additionally, unlike the JS client, Python is a server side language and it's not possible
        # to automatically redirect in browser for the user
        skip_http_redirect = options.get("skip_http_redirect", True)

        if domain:
            response = self._request(
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
            )
            return parse_sso_response(response)
        if provider_id:
            response = self._request(
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
            )
            return parse_sso_response(response)
        raise AuthInvalidCredentialsError(
            "You must provide either a domain or provider_id"
        )

    def sign_in_with_oauth(
        self,
        credentials: SignInWithOAuthCredentials,
    ) -> OAuthResponse:
        """
        Log in an existing user via a third-party provider.
        """
        self._remove_session()

        provider = credentials["provider"]
        options = credentials.get("options", {})
        redirect_to = options.get("redirect_to")
        scopes = options.get("scopes")
        params = options.get("query_params", {})
        if redirect_to:
            params["redirect_to"] = redirect_to
        if scopes:
            params["scopes"] = scopes
        url_with_qs, _ = self._get_url_for_provider(
            f"{self._url}/authorize", provider, params
        )
        return OAuthResponse(provider=provider, url=url_with_qs)

    def link_identity(self, credentials: SignInWithOAuthCredentials) -> OAuthResponse:
        provider = credentials["provider"]
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
        _, query = self._get_url_for_provider(url, provider, params)

        session = self.get_session()
        if not session:
            raise AuthSessionMissingError()

        response = self._request(
            method="GET",
            path=url,
            query=query,
            jwt=session.access_token,
        )
        link_identity = parse_link_identity_response(response)
        return OAuthResponse(provider=provider, url=link_identity.url)

    def get_user_identities(self) -> IdentitiesResponse:
        response = self.get_user()
        if response:
            return IdentitiesResponse(identities=response.user.identities or [])
        raise AuthSessionMissingError()

    def unlink_identity(self, identity: UserIdentity) -> Response:
        session = self.get_session()
        if not session:
            raise AuthSessionMissingError()

        return self._request(
            "DELETE",
            f"user/identities/{identity.identity_id}",
            jwt=session.access_token,
        )

    def sign_in_with_otp(
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
        self._remove_session()
        email = credentials.get("email")
        phone = credentials.get("phone")
        # TODO(@o-santi): this is horrible, but it is the easiest way to satisfy mypy
        #                 it should have been a builder pattern instead, and with proper classes
        if email:
            email_options = cast(
                SignInWithEmailAndPasswordlessCredentialsOptions,
                credentials.get("options", {}),
            )
            email_redirect_to = email_options.get("email_redirect_to")
            should_create_user = email_options.get("should_create_user", True)
            data = email_options.get("data")
            channel = email_options.get("channel", "sms")
            captcha_token = email_options.get("captcha_token")
            response = self._request(
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
            )
            return parse_auth_otp_response(response)
        if phone:
            phone_options = cast(
                SignInWithPhoneAndPasswordlessCredentialsOptions,
                credentials.get("options", {}),
            )
            should_create_user = phone_options.get("should_create_user", True)
            data = phone_options.get("data")
            channel = phone_options.get("channel", "sms")
            captcha_token = phone_options.get("captcha_token")
            response = self._request(
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
            )
            return parse_auth_otp_response(response)
        raise AuthInvalidCredentialsError(
            "You must provide either an email or phone number"
        )

    def resend(
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
        email_redirect_to: Optional[str] = options.get("email_redirect_to")  # type: ignore
        captcha_token = options.get("captcha_token")
        body: Dict[str, object] = {  # improve later
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

        response = self._request(
            "POST",
            "resend",
            body=body,
            redirect_to=email_redirect_to if email else None,
        )
        return parse_auth_otp_response(response)

    def verify_otp(self, params: VerifyOtpParams) -> AuthResponse:
        """
        Log in a user given a User supplied OTP received via mobile.
        """
        self._remove_session()
        response = self._request(
            "POST",
            "verify",
            body={
                "gotrue_meta_security": {
                    "captcha_token": params.get("options", {}).get("captcha_token"),
                },
                **params,
            },
            redirect_to=params.get("options", {}).get("redirect_to"),
        )
        auth_response = parse_auth_response(response)
        if auth_response.session:
            self._save_session(auth_response.session)
            self._notify_all_subscribers("SIGNED_IN", auth_response.session)
        return auth_response

    def reauthenticate(self) -> AuthResponse:
        session = self.get_session()
        if not session:
            raise AuthSessionMissingError()

        self._request(
            "GET",
            "reauthenticate",
            jwt=session.access_token,
        )
        return AuthResponse(user=None, session=None)

    def get_session(self) -> Optional[Session]:
        """
        Returns the session, refreshing it if necessary.

        The session returned can be null if the session is not detected which
        can happen in the event a user is not signed-in or has logged out.
        """
        current_session: Optional[Session] = None
        if self._persist_session:
            maybe_session = self._storage.get_item(self._storage_key)
            current_session = self._get_valid_session(maybe_session)
            if not current_session:
                self._remove_session()
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
            self._call_refresh_token(current_session.refresh_token)
            if has_expired
            else current_session
        )

    def get_user(self, jwt: Optional[str] = None) -> Optional[UserResponse]:
        """
        Gets the current user details if there is an existing session.

        Takes in an optional access token `jwt`. If no `jwt` is provided,
        `get_user()` will attempt to get the `jwt` from the current session.
        """
        if not jwt:
            session = self.get_session()
            if session:
                jwt = session.access_token
            else:
                return None
        return parse_user_response(self._request("GET", "user", jwt=jwt))

    def update_user(
        self, attributes: UserAttributes, options: Optional[UpdateUserOptions] = None
    ) -> UserResponse:
        """
        Updates user data, if there is a logged in user.
        """
        session = self.get_session()
        if not session:
            raise AuthSessionMissingError()
        update_options = options or {}
        response = self._request(
            "PUT",
            "user",
            body=attributes,
            redirect_to=update_options.get("email_redirect_to"),
            jwt=session.access_token,
        )
        user_response = parse_user_response(response)
        session.user = user_response.user
        self._save_session(session)
        self._notify_all_subscribers("USER_UPDATED", session)
        return user_response

    def set_session(self, access_token: str, refresh_token: str) -> AuthResponse:
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
            response = self._refresh_access_token(refresh_token)
            if not response.session:
                return AuthResponse()
            session = response.session
        else:
            user_response = self.get_user(access_token)
            if user_response is None:
                raise UserDoesntExist(access_token)
            session = Session(
                access_token=access_token,
                refresh_token=refresh_token,
                user=user_response.user,
                token_type="bearer",
                expires_in=expires_at - time_now,
                expires_at=expires_at,
            )
        self._save_session(session)
        self._notify_all_subscribers("TOKEN_REFRESHED", session)
        return AuthResponse(session=session, user=session.user)

    def refresh_session(self, refresh_token: Optional[str] = None) -> AuthResponse:
        """
        Returns a new session, regardless of expiry status.

        Takes in an optional current session. If not passed in, then refreshSession()
        will attempt to retrieve it from getSession(). If the current session's
        refresh token is invalid, an error will be thrown.
        """
        if not refresh_token:
            session = self.get_session()
            if session:
                refresh_token = session.refresh_token
        if not refresh_token:
            raise AuthSessionMissingError()
        session = self._call_refresh_token(refresh_token)
        return AuthResponse(session=session, user=session.user)

    def sign_out(self, options: Optional[SignOutOptions] = None) -> None:
        """
        `sign_out` will remove the logged in user from the
        current session and log them out - removing all items from storage and then trigger a `"SIGNED_OUT"` event.

        For advanced use cases, you can revoke all refresh tokens for a user by passing a user's JWT through to `admin.sign_out`.

        There is no way to revoke a user's access token jwt until it expires.
        It is recommended to set a shorter expiry on the jwt for this reason.
        """
        signout_options = options or {"scope": "global"}
        with suppress(AuthApiError):
            session = self.get_session()
            access_token = session.access_token if session else None
            if access_token:
                self.admin.sign_out(access_token, signout_options["scope"])

        if signout_options["scope"] != "others":
            self._remove_session()
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

    def reset_password_for_email(
        self, email: str, options: Optional[Options] = None
    ) -> None:
        """
        Sends a password reset request to an email address.
        """
        reset_options = options or {}
        self._request(
            "POST",
            "recover",
            body={
                "email": email,
                "gotrue_meta_security": {
                    "captcha_token": reset_options.get("captcha_token"),
                },
            },
            redirect_to=reset_options.get("redirect_to"),
        )

    def reset_password_email(
        self,
        email: str,
        options: Optional[Options] = None,
    ) -> None:
        """
        Sends a password reset request to an email address.
        """

        self.reset_password_for_email(email, options or {})

    # MFA methods

    def _enroll(self, params: MFAEnrollParams) -> AuthMFAEnrollResponse:
        session = self.get_session()
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

        response = self._request(
            "POST",
            "factors",
            body=body,
            jwt=session.access_token,
        )
        auth_response = model_validate(AuthMFAEnrollResponse, response.content)
        if params["factor_type"] == "totp" and auth_response.totp:
            auth_response.totp.qr_code = (
                f"data:image/svg+xml;utf-8,{auth_response.totp.qr_code}"
            )
        return auth_response

    def _challenge(self, params: MFAChallengeParams) -> AuthMFAChallengeResponse:
        session = self.get_session()
        if not session:
            raise AuthSessionMissingError()
        response = self._request(
            "POST",
            f"factors/{params.get('factor_id')}/challenge",
            body={"channel": params.get("channel")},
            jwt=session.access_token,
        )
        return model_validate(AuthMFAChallengeResponse, response.content)

    def _challenge_and_verify(
        self,
        params: MFAChallengeAndVerifyParams,
    ) -> AuthMFAVerifyResponse:
        response = self._challenge(
            {
                "factor_id": params["factor_id"],
            }
        )
        return self._verify(
            {
                "factor_id": params["factor_id"],
                "challenge_id": response.id,
                "code": params["code"],
            }
        )

    def _verify(self, params: MFAVerifyParams) -> AuthMFAVerifyResponse:
        session = self.get_session()
        if not session:
            raise AuthSessionMissingError()
        response = self._request(
            "POST",
            f"factors/{params.get('factor_id')}/verify",
            body=params,
            jwt=session.access_token,
        )
        auth_response = model_validate(AuthMFAVerifyResponse, response.content)
        session = model_validate(Session, response.content)
        self._save_session(session)
        self._notify_all_subscribers("MFA_CHALLENGE_VERIFIED", session)
        return auth_response

    def _unenroll(self, params: MFAUnenrollParams) -> AuthMFAUnenrollResponse:
        session = self.get_session()
        if not session:
            raise AuthSessionMissingError()
        response = self._request(
            "DELETE",
            f"factors/{params.get('factor_id')}",
            jwt=session.access_token,
        )
        return model_validate(AuthMFAUnenrollResponse, response.content)

    def _list_factors(self) -> AuthMFAListFactorsResponse:
        response = self.get_user()
        factors = response.user.factors or [] if response else []
        totp = [
            f for f in factors if f.factor_type == "totp" and f.status == "verified"
        ]
        phone = [
            f for f in factors if f.factor_type == "phone" and f.status == "verified"
        ]
        return AuthMFAListFactorsResponse(all=factors, totp=totp, phone=phone)

    def _get_authenticator_assurance_level(
        self,
    ) -> AuthMFAGetAuthenticatorAssuranceLevelResponse:
        session = self.get_session()
        if not session:
            return AuthMFAGetAuthenticatorAssuranceLevelResponse(
                current_level=None,
                next_level=None,
                current_authentication_methods=[],
            )
        payload = decode_jwt(session.access_token)["payload"]
        current_level = payload.get("aal")
        verified_factors = [
            f for f in session.user.factors or [] if f.status == "verified"
        ]
        next_level = "aal2" if verified_factors else current_level
        amr_dict_list = payload.get("amr") or []
        current_authentication_methods = [
            AMREntry.model_validate(amr) for amr in amr_dict_list
        ]
        return AuthMFAGetAuthenticatorAssuranceLevelResponse(
            current_level=current_level,
            next_level=next_level,
            current_authentication_methods=current_authentication_methods,
        )

    # Private methods

    def _remove_session(self) -> None:
        if self._persist_session:
            self._storage.remove_item(self._storage_key)
        else:
            self._in_memory_session = None
        if self._refresh_token_timer:
            self._refresh_token_timer.cancel()
            self._refresh_token_timer = None

    def _get_session_from_url(
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
        user = self.get_user(access_token)
        if user is None:
            raise UserDoesntExist(access_token)
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

    def _recover_and_refresh(self) -> None:
        raw_session = self._storage.get_item(self._storage_key)
        current_session = self._get_valid_session(raw_session)
        if not current_session:
            if raw_session:
                self._remove_session()
            return
        time_now = round(time.time())
        expires_at = current_session.expires_at
        if expires_at and expires_at < time_now + EXPIRY_MARGIN:
            refresh_token = current_session.refresh_token
            if self._auto_refresh_token and refresh_token:
                self._network_retries += 1
                try:
                    self._call_refresh_token(refresh_token)
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
            self._remove_session()
            return
        if self._persist_session:
            self._save_session(current_session)
        self._notify_all_subscribers("SIGNED_IN", current_session)

    def _call_refresh_token(self, refresh_token: str) -> Session:
        if not refresh_token:
            raise AuthSessionMissingError()
        response = self._refresh_access_token(refresh_token)
        if not response.session:
            raise AuthSessionMissingError()
        self._save_session(response.session)
        self._notify_all_subscribers("TOKEN_REFRESHED", response.session)
        return response.session

    def _refresh_access_token(self, refresh_token: str) -> AuthResponse:
        response = self._request(
            "POST",
            "token",
            query=QueryParams(grant_type="refresh_token"),
            body={"refresh_token": refresh_token},
        )
        return parse_auth_response(response)

    def _save_session(self, session: Session) -> None:
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
            self._start_auto_refresh_token(value)
        if self._persist_session and session.expires_at:
            self._storage.set_item(self._storage_key, model_dump_json(session))

    def _start_auto_refresh_token(self, value: float) -> None:
        if self._refresh_token_timer:
            self._refresh_token_timer.cancel()
            self._refresh_token_timer = None
        if value <= 0 or not self._auto_refresh_token:
            return

        def refresh_token_function() -> None:
            self._network_retries += 1
            try:
                session = self.get_session()
                if session:
                    self._call_refresh_token(session.refresh_token)
                    self._network_retries = 0
            except Exception as e:
                if (
                    isinstance(e, AuthRetryableError)
                    and self._network_retries < MAX_RETRIES
                ):
                    self._start_auto_refresh_token(
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
        try:
            session = model_validate(Session, raw_session)
            if session.expires_at is None:
                return None
            return session
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

    def _get_url_for_provider(
        self,
        url: str,
        provider: Provider,
        params: Dict[str, str],
    ) -> Tuple[str, QueryParams]:
        query = QueryParams(params)
        if self._flow_type == "pkce":
            code_verifier = generate_pkce_verifier()
            code_challenge = generate_pkce_challenge(code_verifier)
            self._storage.set_item(f"{self._storage_key}-code-verifier", code_verifier)
            code_challenge_method = (
                "plain" if code_verifier == code_challenge else "s256"
            )
            query = query.set("code_challenge", code_challenge).set(
                "code_challenge_method", code_challenge_method
            )
        query = query.set("provider", provider)
        return f"{url}?{query}", query

    def exchange_code_for_session(self, params: CodeExchangeParams) -> AuthResponse:
        code_verifier = params.get("code_verifier") or self._storage.get_item(
            f"{self._storage_key}-code-verifier"
        )
        response = self._request(
            "POST",
            "token",
            query=QueryParams(grant_type="pkce"),
            body={
                "auth_code": params.get("auth_code"),
                "code_verifier": code_verifier,
            },
            redirect_to=params.get("redirect_to"),
        )
        auth_response = parse_auth_response(response)
        self._storage.remove_item(f"{self._storage_key}-code-verifier")
        if auth_response.session:
            self._save_session(auth_response.session)
            self._notify_all_subscribers("SIGNED_IN", auth_response.session)
        return auth_response

    def _fetch_jwks(self, kid: str, jwks: JWKSet) -> JWK:
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
        response = self._request("GET", ".well-known/jwks.json")
        jwks = parse_jwks(response)
        if response:
            self._jwks = jwks
            self._jwks_cached_at = time.time()

            # find the signing key
            jwk = next((jwk for jwk in jwks["keys"] if jwk["kid"] == kid), None)
            if not jwk:
                raise AuthInvalidJwtError("No matching signing key found in JWKS")

            return jwk

        raise AuthInvalidJwtError("JWT has no valid kid")

    def get_claims(
        self, jwt: Optional[str] = None, jwks: Optional[JWKSet] = None
    ) -> Optional[ClaimsResponse]:
        token = jwt
        if not token:
            session = self.get_session()
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
            self.get_user(token)
            return ClaimsResponse(claims=payload, headers=header, signature=signature)

        algorithm = get_algorithm_by_name(header["alg"])
        jwk_set = self._fetch_jwks(header["kid"], jwks or {"keys": []})
        signing_key = algorithm.from_jwk(cast(Dict[str, str], jwk_set))

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
            except Exception:
                # Ignore errors if event loop is closed or selector is not registered
                pass
            finally:
                # Always set to None to prevent further attempts
                self._refresh_token_timer = None
