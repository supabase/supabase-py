from __future__ import annotations

import time
from dataclasses import dataclass
from types import TracebackType
from typing import Callable, Generic, Literal
from uuid import uuid4

from jwt import get_algorithm_by_name
from supabase_utils.http.headers import Headers
from supabase_utils.http.io import (
    AsyncHttpIO,
    AsyncHttpSession,
    HttpIO,
    HttpMethod,
    HttpSession,
    SyncHttpIO,
    handle_http_io,
)
from supabase_utils.http.query import URLQuery
from supabase_utils.http.request import EmptyRequest, JSONRequest, Response
from supabase_utils.types import JSON
from yarl import URL

from .errors import (
    AuthImplicitGrantRedirectError,
    AuthInvalidJwtError,
    AuthSessionMissingError,
    UserDoesntExist,
)
from .helpers import (
    decode_jwt,
    generate_pkce_challenge,
    generate_pkce_verifier,
    handle_error_response,
    parse_auth_otp_response,
    parse_auth_response,
    parse_jwks,
    parse_link_identity_response,
    parse_sso_response,
    parse_user_response,
    redirect_to_as_query,
    validate_exp,
)
from .mfa import AsyncSupabaseAuthMFAClient, SyncSupabaseAuthMFAClient
from .session import (
    AsyncMemoryStorage,
    AsyncSessionManager,
    AsyncSupportedStorage,
    SessionManagerCommon,
    SyncMemoryStorage,
    SyncSessionManager,
    SyncSupportedStorage,
)
from .types import (
    JWK,
    AuthChangeEvent,
    AuthFlowType,
    AuthOtpResponse,
    AuthResponse,
    ClaimsResponse,
    IdentitiesResponse,
    JWKSet,
    OAuthResponse,
    Provider,
    ResendCredentials,
    ResendEmailCredentials,
    Session,
    SignInWithEmailAndPasswordlessCredentials,
    SignInWithPasswordCredentials,
    SignInWithPasswordlessCredentials,
    SignInWithSSOCredentials,
    SignOutScope,
    SignUpWithEmailAndPasswordCredentials,
    SignUpWithPasswordCredentials,
    SSOResponse,
    Subscription,
    UserAttributes,
    UserIdentity,
    UserResponse,
    VerifyOtpParams,
    VerifyTokenHashParams,
)


def is_implicit_grant_flow(url: URL) -> bool:
    params = url.query
    return "access_token" in params or "error_description" in params


@dataclass
class SupabaseAuthHttpClient(Generic[HttpIO]):
    executor: HttpIO
    base_url: URL
    default_headers: Headers
    session_manager: SessionManagerCommon[HttpIO]
    _jwks: JWKSet
    flow_type: AuthFlowType = "implicit"
    _jwks_ttl: float = 600  # 10 minutes
    _jwks_cached_at: float | None = None

    @handle_http_io
    def _sign_in_anonymously(
        self, data: JSON = None, captcha_token: str | None = None
    ) -> HttpMethod[AuthResponse]:
        """
        Creates a new anonymous user.
        """
        response = yield JSONRequest(
            method="POST",
            path=["signup"],
            body={
                "data": data,
                "gotrue_meta_security": {
                    "captcha_token": captcha_token,
                },
            },
        )
        return parse_auth_response(response)

    @handle_http_io
    def _sign_up(
        self,
        credentials: SignUpWithPasswordCredentials,
    ) -> HttpMethod[AuthResponse]:
        """
        Creates a new user.
        """
        if isinstance(credentials, SignUpWithEmailAndPasswordCredentials):
            query = redirect_to_as_query(credentials.redirect_to)
        else:
            query = URLQuery.empty()
        response = yield JSONRequest(
            method="POST", path=["signup"], body=credentials.body, query=query
        )
        auth_response = parse_auth_response(response)
        return auth_response

    @handle_http_io
    def _sign_in_with_password(
        self,
        credentials: SignInWithPasswordCredentials,
    ) -> HttpMethod[AuthResponse]:
        """
        Log in an existing user with an email or phone and password.
        """
        response = yield JSONRequest(
            method="POST",
            path=["token"],
            body=credentials,
            query=URLQuery.from_mapping({"grant_type": "password"}),
        )
        auth_response = parse_auth_response(response)
        return auth_response

    @handle_http_io
    def _sign_in_with_id_token(
        self,
        provider: Literal["google", "apple", "azure", "facebook", "kakao"],
        token: str,
        access_token: str | None = None,
        nonce: str | None = None,
        captcha_token: str | None = None,
    ) -> HttpMethod[AuthResponse]:
        """
        Allows signing in with an OIDC ID token. The authentication provider used should be enabled and configured.
        """
        response = yield JSONRequest(
            method="POST",
            path=["token"],
            body={
                "provider": provider,
                "id_token": token,
                "access_token": access_token,
                "nonce": nonce,
                "gotrue_meta_security": {
                    "captcha_token": captcha_token,
                },
            },
            query=URLQuery.from_mapping({"grant_type": "id_token"}),
        )
        auth_response = parse_auth_response(response)
        return auth_response

    @handle_http_io
    def sign_in_with_sso(
        self, credentials: SignInWithSSOCredentials
    ) -> HttpMethod[SSOResponse]:
        response = yield JSONRequest(
            method="POST",
            path=["sso"],
            body=credentials,
        )
        return parse_sso_response(response)

    @handle_http_io
    def _sign_out(self, session: Session, scope: SignOutScope) -> HttpMethod[None]:
        response = yield EmptyRequest(
            method="POST",
            path=["logout"],
            query=URLQuery.from_mapping({"scope": scope}),
            headers=session.encode_access_token(),
        )
        if not response.is_success:
            raise handle_error_response(response)

    def _sign_in_with_oauth(
        self,
        provider: Provider,
        redirect_to: str | None = None,
        scopes: str | None = None,
        query_params: dict[str, str] | None = None,
    ) -> tuple[OAuthResponse, str | None]:
        """
        Log in an existing user via a third-party provider.
        """
        query = (
            URLQuery.from_mapping(query_params) if query_params else URLQuery.empty()
        )
        if redirect_to:
            query = query.set("redirect_to", redirect_to)
        if scopes:
            query = query.set("scopes", scopes)
        code_verifier, query = self._get_url_for_provider(provider, query)
        new_url = self.base_url.joinpath("authorize").with_query(query.as_query())
        return OAuthResponse(provider=provider, url=str(new_url)), code_verifier

    @handle_http_io
    def _link_identity(
        self,
        session: Session,
        provider: Provider,
        redirect_to: str | None = None,
        scopes: str | None = None,
        query_params: dict[str, str] | None = None,
    ) -> HttpMethod[tuple[OAuthResponse, str | None]]:
        query = (
            URLQuery.from_mapping(query_params) if query_params else URLQuery.empty()
        )
        if redirect_to:
            query = query.set("redirect_to", redirect_to)
        if scopes:
            query = query.set("scopes", scopes)
        query = query.set("skip_http_redirect", "true")

        code_verifier, query = self._get_url_for_provider(provider, query)

        response = yield EmptyRequest(
            method="GET",
            path=["user", "identities", "authorize"],
            query=query,
            headers=session.encode_access_token(),
        )
        link_identity = parse_link_identity_response(response)
        return OAuthResponse(provider=provider, url=link_identity.url), code_verifier

    @handle_http_io
    def _unlink_identity(
        self, session: Session, identity: UserIdentity
    ) -> HttpMethod[Response]:
        response = yield EmptyRequest(
            method="DELETE",
            path=["user", "identities", identity.identity_id],
            headers=session.encode_access_token(),
        )
        if not response.is_success:
            raise handle_error_response(response)
        return response

    @handle_http_io
    def _sign_in_with_otp(
        self,
        credentials: SignInWithPasswordlessCredentials,
    ) -> HttpMethod[AuthOtpResponse]:
        if isinstance(credentials, SignInWithEmailAndPasswordlessCredentials):
            query = redirect_to_as_query(credentials.email_redirect_to)
        else:
            query = URLQuery.empty()
        response = yield JSONRequest(
            method="POST",
            path=["otp"],
            body=credentials.body,
            query=query,
        )
        return parse_auth_otp_response(response)

    @handle_http_io
    def resend(
        self,
        credentials: ResendCredentials,
    ) -> HttpMethod[AuthOtpResponse]:
        if isinstance(credentials, ResendEmailCredentials):
            query = redirect_to_as_query(credentials.email_redirect_to)
        else:
            query = URLQuery.empty()
        response = yield JSONRequest(
            method="POST",
            path=["resend"],
            body=credentials.body,
            query=query,
        )
        return parse_auth_otp_response(response)

    @handle_http_io
    def _verify_otp(self, params: VerifyOtpParams) -> HttpMethod[AuthResponse]:
        if isinstance(params, VerifyTokenHashParams):
            query = URLQuery.empty()
        else:
            query = redirect_to_as_query(params.redirect_to)
        response = yield JSONRequest(
            method="POST",
            path=["verify"],
            body=params.body,
            query=query,
        )
        auth_response = parse_auth_response(response)
        return auth_response

    @handle_http_io
    def _reauthenticate(self, session: Session) -> HttpMethod[AuthResponse]:
        response = yield EmptyRequest(
            method="GET",
            path=["reauthenticate"],
            headers=session.encode_access_token(),
        )
        if not response.is_success:
            raise handle_error_response(response)
        return AuthResponse(user=None, session=None)

    @handle_http_io
    def _update_user(
        self,
        session: Session,
        attributes: UserAttributes,
        email_redirect_to: str | None = None,
    ) -> HttpMethod[UserResponse]:
        """
        Updates user data, if there is a logged in user.
        """
        response = yield JSONRequest(
            method="PUT",
            path=["user"],
            body=attributes,
            query=redirect_to_as_query(email_redirect_to),
            headers=session.encode_access_token(),
        )
        user_response = parse_user_response(response)
        session.user = user_response.user
        return user_response

    @handle_http_io
    def _set_session(
        self, access_token: str, refresh_token: str
    ) -> HttpMethod[AuthResponse]:
        time_now = round(time.time())
        expires_at = time_now
        has_expired = True
        session: Session | None = None
        if access_token and access_token.split(".")[1]:
            payload = decode_jwt(access_token).payload
            exp = payload.exp
            if exp:
                has_expired = exp <= time_now
        if has_expired:
            if not refresh_token:
                raise AuthSessionMissingError()
            response = yield from self.session_manager._refresh_access_token(
                refresh_token
            )
            if not response.session:
                return AuthResponse()
            session = response.session
        else:
            user_response = yield from self.session_manager._get_user(access_token)
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
        return AuthResponse(session=session, user=session.user)

    def on_auth_state_change(
        self,
        callback: Callable[[AuthChangeEvent, Session | None], None],
    ) -> Subscription:
        unique_id = str(uuid4())

        def _unsubscribe() -> None:
            self.session_manager.state_change_emitters.pop(unique_id)

        subscription = Subscription(
            id=unique_id,
            callback=callback,
            unsubscribe=_unsubscribe,
        )
        self.session_manager.state_change_emitters[unique_id] = subscription
        return subscription

    @handle_http_io
    def reset_password_for_email(
        self,
        email: str,
        captcha_token: str | None = None,
        redirect_to: str | None = None,
    ) -> HttpMethod[None]:
        """
        Sends a password reset request to an email address.
        """
        response = yield JSONRequest(
            method="POST",
            path=["recover"],
            body={
                "email": email,
                "gotrue_meta_security": {
                    "captcha_token": captcha_token,
                },
            },
            query=redirect_to_as_query(redirect_to),
        )
        if not response.is_success:
            raise handle_error_response(response)

    @handle_http_io
    def _get_session_from_url(
        self,
        url: str,
    ) -> HttpMethod[tuple[Session, str | None]]:
        result = URL(url)
        if not is_implicit_grant_flow(result):
            raise AuthImplicitGrantRedirectError("Not a valid implicit grant flow url.")
        params = result.query
        error_description = params.get("error_description")
        if error_description:
            error_code = params.get("error_code")
            error = params.get("error")
            if not error_code:
                raise AuthImplicitGrantRedirectError("No error_code detected.")
            if not error:
                raise AuthImplicitGrantRedirectError("No error detected.")
            raise AuthImplicitGrantRedirectError(
                error_description,
                code=error_code,
                error=error,
            )
        provider_token = params.get("provider_token")
        provider_refresh_token = params.get("provider_refresh_token")
        access_token = params.get("access_token")
        if not access_token:
            raise AuthImplicitGrantRedirectError("No access_token detected.")
        expires_in = params.get("expires_in")
        if not expires_in:
            raise AuthImplicitGrantRedirectError("No expires_in detected.")
        refresh_token = params.get("refresh_token")
        if not refresh_token:
            raise AuthImplicitGrantRedirectError("No refresh_token detected.")
        token_type = params.get("token_type")
        if not token_type:
            raise AuthImplicitGrantRedirectError("No token_type detected.")
        time_now = round(time.time())
        expires_at = time_now + int(expires_in)
        user = yield from self.session_manager._get_user(access_token)
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
        redirect_type = params.get("type")
        return session, redirect_type

    def _get_url_for_provider(
        self,
        provider: Provider,
        query: URLQuery,
    ) -> tuple[str | None, URLQuery]:
        code_verifier = None
        if self.flow_type == "pkce":
            code_verifier = generate_pkce_verifier()
            code_challenge = generate_pkce_challenge(code_verifier)
            code_challenge_method = (
                "plain" if code_verifier == code_challenge else "s256"
            )
            query = query.set("code_challenge", code_challenge).set(
                "code_challenge_method", code_challenge_method
            )
        query = query.set("provider", provider)
        return code_verifier, query

    @handle_http_io
    def exchange_code_for_session(
        self, code_verifier: str, auth_code: str, redirect_to: str | None = None
    ) -> HttpMethod[AuthResponse]:
        query = redirect_to_as_query(redirect_to).set("grant_type", "pkce")
        response = yield JSONRequest(
            method="POST",
            path=["token"],
            body={
                "auth_code": auth_code,
                "code_verifier": code_verifier,
            },
            query=query,
        )
        auth_response = parse_auth_response(response)
        return auth_response

    def _fetch_jwks(self, kid: str, jwks: JWKSet) -> HttpMethod[JWK]:
        jwk: JWK | None = None

        # try fetching from the suplied keys.
        jwk = next((jwk for jwk in jwks.keys if jwk.kid == kid), None)

        if jwk:
            return jwk

        if self._jwks and (
            self._jwks_cached_at and time.time() - self._jwks_cached_at < self._jwks_ttl
        ):
            # try fetching from the cache.
            jwk = next(
                (jwk for jwk in self._jwks.keys if jwk.kid == kid),
                None,
            )
            if jwk:
                return jwk

        # jwk isn't cached in memory so we need to fetch it from the well-known endpoint
        response = yield EmptyRequest(method="GET", path=[".well-known", "jwks.json"])
        jwks = parse_jwks(response)
        if not response:
            raise AuthInvalidJwtError("JWT has no valid kid")

        self._jwks = jwks
        self._jwks_cached_at = time.time()

        # find the signing key
        jwk = next((jwk for jwk in jwks.keys if jwk.kid == kid), None)
        if not jwk:
            raise AuthInvalidJwtError("No matching signing key found in JWKS")
        return jwk

    @handle_http_io
    def _get_claims(
        self, jwt: str, jwks: JWKSet | None = None
    ) -> HttpMethod[ClaimsResponse]:
        decoded_jwt = decode_jwt(jwt)

        validate_exp(decoded_jwt.payload.exp)
        header = decoded_jwt.header
        payload = decoded_jwt.payload
        signature = decoded_jwt.signature
        # if symmetric algorithm, fallback to get_user
        if not header.kid or header.alg == "HS256":
            yield from self.session_manager._get_user(jwt)
            return ClaimsResponse(
                claims=decoded_jwt.payload,
                headers=decoded_jwt.header,
                signature=decoded_jwt.signature,
            )

        algorithm = get_algorithm_by_name(header.alg)
        jwk_set = yield from self._fetch_jwks(header.kid, jwks or JWKSet(keys=[]))
        signing_key = algorithm.from_jwk(dict(jwk_set))

        # verify the signature
        is_valid = algorithm.verify(
            msg=f"{decoded_jwt.raw_header}.{decoded_jwt.raw_payload}".encode(),
            key=signing_key,
            sig=signature,
        )

        if not is_valid:
            raise AuthInvalidJwtError("Invalid JWT signature")

        # If verification succeeds, decode and return claims
        return ClaimsResponse(claims=payload, headers=header, signature=signature)


class AsyncSupabaseAuthClient(SupabaseAuthHttpClient[AsyncHttpIO]):
    def __init__(
        self,
        url: str,
        http_session: AsyncHttpSession,
        *,
        headers: dict[str, str] | None = None,
        storage_key: str | None = None,
        auto_refresh_token: bool = True,
        persist_session: bool = True,
        storage: AsyncSupportedStorage | None = None,
        flow_type: AuthFlowType = "implicit",
    ) -> None:
        self.base_url = URL(url)
        default_headers = Headers.from_mapping(headers) if headers else Headers.empty()
        executor = AsyncHttpIO(session=http_session)
        self.session_manager: AsyncSessionManager = AsyncSessionManager(
            base_url=self.base_url,
            executor=executor,
            default_headers=default_headers,
            storage=storage or AsyncMemoryStorage(),
            state_change_emitters={},
            auto_refresh_token=auto_refresh_token,
        )
        SupabaseAuthHttpClient.__init__(
            self,
            base_url=self.base_url,
            executor=executor,
            default_headers=default_headers,
            session_manager=self.session_manager,
            _jwks=JWKSet(keys=[]),
            flow_type=flow_type,
        )
        self.mfa = AsyncSupabaseAuthMFAClient(
            base_url=self.base_url,
            executor=executor,
            default_headers=default_headers,
            session_manager=self.session_manager,
        )

    async def __aenter__(self) -> AsyncSupabaseAuthClient:
        await self.executor.session.__aenter__()
        await self.session_manager.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[Exception] | None,
        exc: Exception | None,
        tb: TracebackType | None,
    ) -> None:
        await self.executor.session.__aexit__(exc_type, exc, tb)
        await self.session_manager.__aexit__(exc_type, exc, tb)

    # Initializations

    async def initialize(self, *, url: str | None = None) -> None:
        if url and is_implicit_grant_flow(URL(url)):
            await self.initialize_from_url(url)
        else:
            await self.initialize_from_storage()

    async def initialize_from_storage(self) -> None:
        return await self.session_manager.recover_and_refresh()

    async def initialize_from_url(self, url: str) -> None:
        try:
            if is_implicit_grant_flow(URL(url)):
                session, redirect_type = await self._get_session_from_url(url)
                await self.session_manager.save_session(session)
                self.session_manager.notify_all_subscribers("SIGNED_IN", session)
                if redirect_type == "recovery":
                    self.session_manager.notify_all_subscribers(
                        "PASSWORD_RECOVERY", session
                    )
        except Exception as e:
            await self.session_manager.remove_session()
            raise e

    async def save_session_and_sign_in(self, auth_response: AuthResponse) -> None:
        await self.session_manager.remove_session()
        if auth_response.session:
            await self.session_manager.save_session(auth_response.session)
            self.session_manager.notify_all_subscribers(
                "SIGNED_IN", auth_response.session
            )

    # Public methods

    async def sign_in_anonymously(
        self, data: JSON = None, captcha_token: str | None = None
    ) -> AuthResponse:
        """
        Creates a new anonymous user.
        """
        auth_response = await self._sign_in_anonymously(data, captcha_token)
        await self.save_session_and_sign_in(auth_response)
        return auth_response

    async def sign_up(
        self,
        credentials: SignUpWithPasswordCredentials,
    ) -> AuthResponse:
        """
        Creates a new user.
        """
        auth_response = await self._sign_up(credentials)
        await self.save_session_and_sign_in(auth_response)
        return auth_response

    async def sign_in_with_password(
        self,
        credentials: SignInWithPasswordCredentials,
    ) -> AuthResponse:
        """
        Log in an existing user with an email or phone and password.
        """
        auth_response = await self._sign_in_with_password(credentials)
        await self.save_session_and_sign_in(auth_response)
        return auth_response

    async def sign_in_with_id_token(
        self,
        provider: Literal["google", "apple", "azure", "facebook", "kakao"],
        token: str,
        access_token: str | None = None,
        nonce: str | None = None,
        captcha_token: str | None = None,
    ) -> AuthResponse:
        """
        Allows signing in with an OIDC ID token. The authentication provider used should be enabled and configured.
        """
        auth_response = await self._sign_in_with_id_token(
            provider, token, access_token, nonce, captcha_token
        )
        await self.save_session_and_sign_in(auth_response)
        return auth_response

    async def sign_in_with_oauth(
        self,
        provider: Provider,
        redirect_to: str | None = None,
        scopes: str | None = None,
        query_params: dict[str, str] | None = None,
    ) -> OAuthResponse:
        """
        Log in an existing user via a third-party provider.
        """
        await self.session_manager.remove_session()
        oauth_response, code_verifier = self._sign_in_with_oauth(
            provider, redirect_to, scopes, query_params
        )
        if code_verifier:
            key = f"{self.session_manager.storage_key}-code-verifier"
            await self.session_manager.storage.set_item(key, code_verifier)
        return oauth_response

    async def link_identity(
        self,
        provider: Provider,
        redirect_to: str | None = None,
        scopes: str | None = None,
        query_params: dict[str, str] | None = None,
    ) -> OAuthResponse:
        session = await self.session_manager.get_session_or_raise()
        oauth_response, code_verifier = await self._link_identity(
            session, provider, redirect_to, scopes, query_params
        )
        if code_verifier:
            key = f"{self.session_manager.storage_key}-code-verifier"
            await self.session_manager.storage.set_item(key, code_verifier)
        return oauth_response

    async def get_user_identities(self) -> IdentitiesResponse:
        response = await self.get_user()
        if not response:
            raise AuthSessionMissingError()
        return IdentitiesResponse(identities=response.user.identities or [])

    async def unlink_identity(self, identity: UserIdentity) -> Response:
        session = await self.session_manager.get_session_or_raise()
        return await self._unlink_identity(session, identity)

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
        await self.session_manager.remove_session()
        return await self._sign_in_with_otp(credentials)

    async def verify_otp(self, params: VerifyOtpParams) -> AuthResponse:
        """
        Log in a user given a User supplied OTP received via mobile.
        """
        auth_response = await self._verify_otp(params)
        await self.save_session_and_sign_in(auth_response)
        return auth_response

    async def reauthenticate(self) -> AuthResponse:
        session = await self.session_manager.get_session_or_raise()
        return await self._reauthenticate(session)

    async def get_session(self) -> Session | None:
        """
        Returns the session, refreshing it if necessary.

        The session returned can be null if the session is not detected which
        can happen in the event a user is not signed-in or has logged out.
        """
        return await self.session_manager.get_session()

    async def get_user(self, jwt: str | None = None) -> UserResponse | None:
        """
        Gets the current user details if there is an existing session.

        Takes in an optional access token `jwt`. If no `jwt` is provided,
        `get_user()` will attempt to get the `jwt` from the current session.
        """
        if not jwt:
            session = await self.get_session()
            if not session:
                return None
            jwt = session.access_token
        return await self.session_manager.get_user(jwt)

    async def update_user(
        self, attributes: UserAttributes, email_redirect_to: str | None = None
    ) -> UserResponse:
        """
        Updates user data, if there is a logged in user.
        """
        session = await self.session_manager.get_session_or_raise()
        user_response = await self._update_user(session, attributes, email_redirect_to)
        await self.session_manager.save_session(session)
        self.session_manager.notify_all_subscribers("USER_UPDATED", session)
        return user_response

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
        auth_response = await self._set_session(access_token, refresh_token)
        if auth_response.session:
            await self.session_manager.save_session(auth_response.session)
            self.session_manager.notify_all_subscribers(
                "TOKEN_REFRESHED", auth_response.session
            )
        return auth_response

    async def refresh_session(self, refresh_token: str | None = None) -> AuthResponse:
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
        session = await self.session_manager.call_refresh_token(refresh_token)
        return AuthResponse(session=session, user=session.user)

    async def sign_out(self, scope: SignOutScope = "global") -> None:
        """
        `sign_out` will remove the logged in user from the
        current session and log them out - removing all items from storage and then trigger a `"SIGNED_OUT"` event.

        For advanced use cases, you can revoke all refresh tokens for a user by passing a user's JWT through to `admin.sign_out`.

        There is no way to revoke a user's access token jwt until it expires.
        It is recommended to set a shorter expiry on the jwt for this reason.
        """
        session = await self.get_session()
        if session:
            await self._sign_out(session, scope)

        if scope != "others":
            await self.session_manager.remove_session()
            self.session_manager.notify_all_subscribers("SIGNED_OUT", None)

    def on_auth_state_change(
        self,
        callback: Callable[[AuthChangeEvent, Session | None], None],
    ) -> Subscription:
        """
        Receive a notification every time an auth event happens.
        """
        unique_id = str(uuid4())

        def _unsubscribe() -> None:
            self.session_manager.state_change_emitters.pop(unique_id)

        subscription = Subscription(
            id=unique_id,
            callback=callback,
            unsubscribe=_unsubscribe,
        )
        self.session_manager.state_change_emitters[unique_id] = subscription
        return subscription

    async def get_claims(
        self, jwt: str | None = None, jwks: JWKSet | None = None
    ) -> ClaimsResponse | None:
        if not jwt:
            session = await self.get_session()
            if not session:
                return None
            jwt = session.access_token
        return await self._get_claims(jwt, jwks)


class SyncSupabaseAuthClient(SupabaseAuthHttpClient[SyncHttpIO]):
    def __init__(
        self,
        url: str,
        http_session: HttpSession,
        *,
        headers: dict[str, str] | None = None,
        storage_key: str | None = None,
        auto_refresh_token: bool = True,
        persist_session: bool = True,
        storage: SyncSupportedStorage | None = None,
        flow_type: AuthFlowType = "implicit",
    ) -> None:
        self.base_url = URL(url)
        default_headers = Headers.from_mapping(headers) if headers else Headers.empty()
        executor = SyncHttpIO(session=http_session)
        self.session_manager: SyncSessionManager = SyncSessionManager(
            base_url=self.base_url,
            executor=executor,
            default_headers=default_headers,
            storage=storage or SyncMemoryStorage(),
            state_change_emitters={},
            auto_refresh_token=auto_refresh_token,
        )
        SupabaseAuthHttpClient.__init__(
            self,
            base_url=self.base_url,
            executor=executor,
            default_headers=default_headers,
            session_manager=self.session_manager,
            _jwks=JWKSet(keys=[]),
            flow_type=flow_type,
        )
        self.mfa = SyncSupabaseAuthMFAClient(
            base_url=self.base_url,
            executor=executor,
            default_headers=default_headers,
            session_manager=self.session_manager,
        )

    def __enter__(self) -> SyncSupabaseAuthClient:
        self.executor.session.__enter__()
        self.session_manager.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[Exception] | None,
        exc: Exception | None,
        tb: TracebackType | None,
    ) -> None:
        self.executor.session.__exit__(exc_type, exc, tb)
        self.session_manager.__exit__(exc_type, exc, tb)

    # Initializations

    def initialize(self, *, url: str | None = None) -> None:
        if url and is_implicit_grant_flow(URL(url)):
            self.initialize_from_url(url)
        else:
            self.initialize_from_storage()

    def initialize_from_storage(self) -> None:
        return self.session_manager.recover_and_refresh()

    def initialize_from_url(self, url: str) -> None:
        try:
            if is_implicit_grant_flow(URL(url)):
                session, redirect_type = self._get_session_from_url(url)
                self.session_manager.save_session(session)
                self.session_manager.notify_all_subscribers("SIGNED_IN", session)
                if redirect_type == "recovery":
                    self.session_manager.notify_all_subscribers(
                        "PASSWORD_RECOVERY", session
                    )
        except Exception as e:
            self.session_manager.remove_session()
            raise e

    def save_session_and_sign_in(self, auth_response: AuthResponse) -> None:
        self.session_manager.remove_session()
        if auth_response.session:
            self.session_manager.save_session(auth_response.session)
            self.session_manager.notify_all_subscribers(
                "SIGNED_IN", auth_response.session
            )

    # Public methods

    def sign_in_anonymously(
        self, data: JSON = None, captcha_token: str | None = None
    ) -> AuthResponse:
        """
        Creates a new anonymous user.
        """
        auth_response = self._sign_in_anonymously(data, captcha_token)
        self.save_session_and_sign_in(auth_response)
        return auth_response

    def sign_up(
        self,
        credentials: SignUpWithPasswordCredentials,
    ) -> AuthResponse:
        """
        Creates a new user.
        """
        auth_response = self._sign_up(credentials)
        self.save_session_and_sign_in(auth_response)
        return auth_response

    def sign_in_with_password(
        self,
        credentials: SignInWithPasswordCredentials,
    ) -> AuthResponse:
        """
        Log in an existing user with an email or phone and password.
        """
        auth_response = self._sign_in_with_password(credentials)
        self.save_session_and_sign_in(auth_response)
        return auth_response

    def sign_in_with_id_token(
        self,
        provider: Literal["google", "apple", "azure", "facebook", "kakao"],
        token: str,
        access_token: str | None = None,
        nonce: str | None = None,
        captcha_token: str | None = None,
    ) -> AuthResponse:
        """
        Allows signing in with an OIDC ID token. The authentication provider used should be enabled and configured.
        """
        auth_response = self._sign_in_with_id_token(
            provider, token, access_token, nonce, captcha_token
        )
        self.save_session_and_sign_in(auth_response)
        return auth_response

    def sign_in_with_oauth(
        self,
        provider: Provider,
        redirect_to: str | None = None,
        scopes: str | None = None,
        query_params: dict[str, str] | None = None,
    ) -> OAuthResponse:
        """
        Log in an existing user via a third-party provider.
        """
        self.session_manager.remove_session()
        oauth_response, code_verifier = self._sign_in_with_oauth(
            provider, redirect_to, scopes, query_params
        )
        if code_verifier:
            key = f"{self.session_manager.storage_key}-code-verifier"
            self.session_manager.storage.set_item(key, code_verifier)
        return oauth_response

    def link_identity(
        self,
        provider: Provider,
        redirect_to: str | None = None,
        scopes: str | None = None,
        query_params: dict[str, str] | None = None,
    ) -> OAuthResponse:
        session = self.session_manager.get_session_or_raise()
        oauth_response, code_verifier = self._link_identity(
            session, provider, redirect_to, scopes, query_params
        )
        if code_verifier:
            key = f"{self.session_manager.storage_key}-code-verifier"
            self.session_manager.storage.set_item(key, code_verifier)
        return oauth_response

    def get_user_identities(self) -> IdentitiesResponse:
        response = self.get_user()
        if not response:
            raise AuthSessionMissingError()
        return IdentitiesResponse(identities=response.user.identities or [])

    def unlink_identity(self, identity: UserIdentity) -> Response:
        session = self.session_manager.get_session_or_raise()
        return self._unlink_identity(session, identity)

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
        self.session_manager.remove_session()
        return self._sign_in_with_otp(credentials)

    def verify_otp(self, params: VerifyOtpParams) -> AuthResponse:
        """
        Log in a user given a User supplied OTP received via mobile.
        """
        auth_response = self._verify_otp(params)
        self.save_session_and_sign_in(auth_response)
        return auth_response

    def reauthenticate(self) -> AuthResponse:
        session = self.session_manager.get_session_or_raise()
        return self._reauthenticate(session)

    def get_session(self) -> Session | None:
        """
        Returns the session, refreshing it if necessary.

        The session returned can be null if the session is not detected which
        can happen in the event a user is not signed-in or has logged out.
        """
        return self.session_manager.get_session()

    def get_user(self, jwt: str | None = None) -> UserResponse | None:
        """
        Gets the current user details if there is an existing session.

        Takes in an optional access token `jwt`. If no `jwt` is provided,
        `get_user()` will attempt to get the `jwt` from the current session.
        """
        if not jwt:
            session = self.get_session()
            if not session:
                return None
            jwt = session.access_token
        return self.session_manager.get_user(jwt)

    def update_user(
        self, attributes: UserAttributes, email_redirect_to: str | None = None
    ) -> UserResponse:
        """
        Updates user data, if there is a logged in user.
        """
        session = self.session_manager.get_session_or_raise()
        user_response = self._update_user(session, attributes, email_redirect_to)
        self.session_manager.save_session(session)
        self.session_manager.notify_all_subscribers("USER_UPDATED", session)
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
        auth_response = self._set_session(access_token, refresh_token)
        if auth_response.session:
            self.session_manager.save_session(auth_response.session)
            self.session_manager.notify_all_subscribers(
                "TOKEN_REFRESHED", auth_response.session
            )
        return auth_response

    def refresh_session(self, refresh_token: str | None = None) -> AuthResponse:
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
        session = self.session_manager.call_refresh_token(refresh_token)
        return AuthResponse(session=session, user=session.user)

    def sign_out(self, scope: SignOutScope = "global") -> None:
        """
        `sign_out` will remove the logged in user from the
        current session and log them out - removing all items from storage and then trigger a `"SIGNED_OUT"` event.

        For advanced use cases, you can revoke all refresh tokens for a user by passing a user's JWT through to `admin.sign_out`.

        There is no way to revoke a user's access token jwt until it expires.
        It is recommended to set a shorter expiry on the jwt for this reason.
        """
        session = self.get_session()
        if session:
            self._sign_out(session, scope)

        if scope != "others":
            self.session_manager.remove_session()
            self.session_manager.notify_all_subscribers("SIGNED_OUT", None)

    def on_auth_state_change(
        self,
        callback: Callable[[AuthChangeEvent, Session | None], None],
    ) -> Subscription:
        """
        Receive a notification every time an auth event happens.
        """
        unique_id = str(uuid4())

        def _unsubscribe() -> None:
            self.session_manager.state_change_emitters.pop(unique_id)

        subscription = Subscription(
            id=unique_id,
            callback=callback,
            unsubscribe=_unsubscribe,
        )
        self.session_manager.state_change_emitters[unique_id] = subscription
        return subscription

    def get_claims(
        self, jwt: str | None = None, jwks: JWKSet | None = None
    ) -> ClaimsResponse | None:
        if not jwt:
            session = self.get_session()
            if not session:
                return None
            jwt = session.access_token
        return self._get_claims(jwt, jwks)
