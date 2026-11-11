from __future__ import annotations

import asyncio
import json
import re
import secrets
import threading
import time
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, NamedTuple, Self, TypeGuard, override

from jwt import get_algorithm_by_name
from pydantic import BaseModel
from supabase_utils.http.errors import SupabaseAPIError
from supabase_utils.http.headers import Headers
from supabase_utils.http.io import (
    AsyncHttpIO,
    AsyncHttpSession,
    HttpMethod,
    HttpSession,
    SyncHttpIO,
    handle_http_io,
)
from supabase_utils.http.query import URLQuery
from supabase_utils.http.request import EmptyRequest, JSONRequest, Response
from yarl import URL

from .constants import STORAGE_KEY
from .errors import (
    AuthImplicitGrantRedirectError,
    AuthInvalidJwtError,
    AuthPKCECodeVerifierMissingError,
    AuthSessionMissingError,
    UserDoesNotExistError,
)
from .helpers import (
    _handle_error_response,
    _redirect_to_as_query,
    decode_jwt,
    generate_pkce_challenge,
    generate_pkce_verifier,
    parse_auth_otp_response,
    parse_auth_response,
    parse_jwks,
    parse_link_identity_response,
    parse_sso_response,
    parse_user_response,
    validate_expiration,
)
from .mfa import AsyncSupabaseAuthMFAClient, SyncSupabaseAuthMFAClient
from .session import (
    AsyncMemoryStorage,
    AsyncSupportedStorage,
    SyncMemoryStorage,
    SyncSupportedStorage,
    _AsyncSessionManager,
    _SessionManagerCommon,
    _SyncSessionManager,
)
from .types import (
    JWK,
    AuthChangeEvent,
    AuthFlowType,
    AuthOtpResponse,
    AuthResponse,
    AuthStateChange,
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
    SignOutReason,
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
from .version import __version__

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable, Generator, Mapping
    from types import TracebackType

    from supabase_utils.http.retry import RetryPolicy
    from supabase_utils.types import JSON


def _is_implicit_grant_flow(url: URL) -> bool:
    params = url.query
    return "access_token" in params or "error_description" in params


_PASSWORD_RECOVERY_SUFFIX = "/PASSWORD_RECOVERY"
_MAX_PENDING_PKCE_FLOWS = 5
_FLOW_ID_PARAMETER = "sb_flow_id"
_FLOW_ID_PATTERN = re.compile(r"[A-Za-z0-9_-]{8,64}")


class _PKCEFlow(NamedTuple):
    flow_id: str
    code_verifier: str


def _is_valid_flow_id(flow_id: object) -> TypeGuard[str]:
    return isinstance(flow_id, str) and _FLOW_ID_PATTERN.fullmatch(flow_id) is not None


def _parse_flow_index(raw: str | None) -> list[str]:
    """The storage may be client controlled, like a cookie, so anything that
    is not a flow id is dropped before it is used in a storage key."""
    if raw is None:
        return []
    try:
        index: object = json.loads(raw)
    except ValueError:
        return []
    if not isinstance(index, list):
        return []
    flow_ids: list[object] = index
    return [flow_id for flow_id in flow_ids if _is_valid_flow_id(flow_id)]


def _append_flow_id(redirect_to: str, flow_id: str) -> str:
    """Edits the URL as a string, so custom schemes and the encoding of the
    other parameters stay as they are."""
    url, hash_sign, fragment = redirect_to.partition("#")
    path, _, query = url.partition("?")
    parameters = [
        parameter
        for parameter in query.split("&")
        if parameter and parameter.partition("=")[0] != _FLOW_ID_PARAMETER
    ]
    parameters.append(f"{_FLOW_ID_PARAMETER}={flow_id}")
    return f"{path}?{'&'.join(parameters)}{hash_sign}{fragment}"


def _push_flow(index: list[str], flow_id: str) -> tuple[list[str], list[str]]:
    index = [pending for pending in index if pending != flow_id] + [flow_id]
    cut = max(len(index) - _MAX_PENDING_PKCE_FLOWS, 0)
    return index[cut:], index[:cut]


def _pkce_challenge_params(code_verifier: str) -> dict[str, str]:
    code_challenge = generate_pkce_challenge(code_verifier)
    code_challenge_method = "plain" if code_verifier == code_challenge else "s256"
    return {
        "code_challenge": code_challenge,
        "code_challenge_method": code_challenge_method,
    }


def _with_pkce_challenge(
    body: BaseModel | dict[str, JSON], pkce_flow: _PKCEFlow | None
) -> BaseModel | dict[str, JSON]:
    if pkce_flow is None:
        return body
    if isinstance(body, BaseModel):
        body = body.model_dump(mode="json", exclude_none=True)
    return {**body, **_pkce_challenge_params(pkce_flow.code_verifier)}


def _strip_password_recovery_suffix(code_verifier: str) -> str:
    return code_verifier.split("/", 1)[0]


@dataclass
class SupabaseAuthHttpClient[
    HttpIO: (SyncHttpIO, AsyncHttpIO),
    SessionManager: _SessionManagerCommon[Any],
]:
    executor: HttpIO
    base_url: URL
    default_headers: Headers
    session_manager: SessionManager
    _jwks: JWKSet
    flow_type: AuthFlowType = "implicit"
    append_flow_id_to_redirects: bool = False
    _jwks_ttl: float = 600  # 10 minutes
    _jwks_cached_at: float | None = None

    def _new_pkce_flow(self) -> _PKCEFlow | None:
        if self.flow_type != "pkce":
            return None
        return _PKCEFlow(
            flow_id=secrets.token_hex(16), code_verifier=generate_pkce_verifier()
        )

    @property
    def _code_verifier_storage_key(self) -> str:
        """Where versions without flow ids stored the verifier."""
        return f"{self.session_manager.storage_key}-code-verifier"

    def _redirect_with_flow_id(
        self, redirect_to: str | None, pkce_flow: _PKCEFlow | None
    ) -> str | None:
        if redirect_to and pkce_flow and self.append_flow_id_to_redirects:
            return _append_flow_id(redirect_to, pkce_flow.flow_id)
        return redirect_to

    @property
    def _flow_index_storage_key(self) -> str:
        return f"{self.session_manager.storage_key}-flows-code-verifier"

    def _flow_storage_key(self, flow_id: str) -> str:
        return f"{self.session_manager.storage_key}-flow-{flow_id}-code-verifier"

    @staticmethod
    def _stored_code_verifier(code_verifier: str, password_recovery: bool) -> str:
        if password_recovery:
            return code_verifier + _PASSWORD_RECOVERY_SUFFIX
        return code_verifier

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
        pkce_flow: _PKCEFlow | None = None,
    ) -> HttpMethod[AuthResponse]:
        """
        Creates a new user.
        """
        body: BaseModel | dict[str, JSON] = credentials.body
        if isinstance(credentials, SignUpWithEmailAndPasswordCredentials):
            query = _redirect_to_as_query(
                self._redirect_with_flow_id(credentials.redirect_to, pkce_flow)
            )
            body = _with_pkce_challenge(body, pkce_flow)
        else:
            query = URLQuery.empty()
        response = yield JSONRequest(
            method="POST", path=["signup"], body=body, query=query
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
    def _sign_in_with_sso(
        self, credentials: SignInWithSSOCredentials, pkce_flow: _PKCEFlow | None = None
    ) -> HttpMethod[SSOResponse]:
        redirect_to = self._redirect_with_flow_id(credentials.redirect_to, pkce_flow)
        if redirect_to != credentials.redirect_to:
            credentials = credentials.model_copy(update={"redirect_to": redirect_to})
        response = yield JSONRequest(
            method="POST",
            path=["sso"],
            body=_with_pkce_challenge(credentials, pkce_flow),
        )
        sso_response = parse_sso_response(response)
        if pkce_flow is None:
            return sso_response
        return sso_response.model_copy(update={"flow_id": pkce_flow.flow_id})

    @handle_http_io
    def _sign_out(self, session: Session, scope: SignOutScope) -> HttpMethod[None]:
        response = yield EmptyRequest(
            method="POST",
            path=["logout"],
            query=URLQuery.from_mapping({"scope": scope}),
            headers=session.encode_access_token(),
        )
        if not response.is_success:
            raise _handle_error_response(response)

    def _sign_in_with_oauth(
        self,
        provider: Provider,
        redirect_to: str | None = None,
        scopes: str | None = None,
        query_params: dict[str, str] | None = None,
    ) -> tuple[OAuthResponse, _PKCEFlow | None]:
        """
        Log in an existing user via a third-party provider.
        """
        pkce_flow = self._new_pkce_flow()
        query = (
            URLQuery.from_mapping(query_params) if query_params else URLQuery.empty()
        )
        redirect_to = self._redirect_with_flow_id(redirect_to, pkce_flow)
        if redirect_to:
            query = query.set("redirect_to", redirect_to)
        if scopes:
            query = query.set("scopes", scopes)
        query = self._get_url_for_provider(provider, query, pkce_flow)
        new_url = self.base_url.joinpath("authorize").with_query(query.as_query())
        oauth_response = OAuthResponse(
            provider=provider,
            url=str(new_url),
            flow_id=pkce_flow.flow_id if pkce_flow else None,
        )
        return oauth_response, pkce_flow

    @handle_http_io
    def _link_identity(
        self,
        session: Session,
        provider: Provider,
        redirect_to: str | None = None,
        scopes: str | None = None,
        query_params: dict[str, str] | None = None,
    ) -> HttpMethod[tuple[OAuthResponse, _PKCEFlow | None]]:
        pkce_flow = self._new_pkce_flow()
        query = (
            URLQuery.from_mapping(query_params) if query_params else URLQuery.empty()
        )
        redirect_to = self._redirect_with_flow_id(redirect_to, pkce_flow)
        if redirect_to:
            query = query.set("redirect_to", redirect_to)
        if scopes:
            query = query.set("scopes", scopes)
        query = query.set("skip_http_redirect", "true")
        query = self._get_url_for_provider(provider, query, pkce_flow)

        response = yield EmptyRequest(
            method="GET",
            path=["user", "identities", "authorize"],
            query=query,
            headers=session.encode_access_token(),
        )
        link_identity = parse_link_identity_response(response)
        oauth_response = OAuthResponse(
            provider=provider,
            url=link_identity.url,
            flow_id=pkce_flow.flow_id if pkce_flow else None,
        )
        return oauth_response, pkce_flow

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
            raise _handle_error_response(response)
        return response

    @handle_http_io
    def _sign_in_with_otp(
        self,
        credentials: SignInWithPasswordlessCredentials,
        pkce_flow: _PKCEFlow | None = None,
    ) -> HttpMethod[AuthOtpResponse]:
        body: BaseModel | dict[str, JSON] = credentials.body
        if isinstance(credentials, SignInWithEmailAndPasswordlessCredentials):
            query = _redirect_to_as_query(
                self._redirect_with_flow_id(credentials.email_redirect_to, pkce_flow)
            )
            body = _with_pkce_challenge(body, pkce_flow)
        else:
            query = URLQuery.empty()
        response = yield JSONRequest(
            method="POST",
            path=["otp"],
            body=body,
            query=query,
        )
        return parse_auth_otp_response(response)

    @handle_http_io
    def _resend(
        self,
        credentials: ResendCredentials,
        pkce_flow: _PKCEFlow | None = None,
    ) -> HttpMethod[AuthOtpResponse]:
        body: BaseModel | dict[str, JSON] = credentials.body
        if isinstance(credentials, ResendEmailCredentials):
            query = _redirect_to_as_query(
                self._redirect_with_flow_id(credentials.email_redirect_to, pkce_flow)
            )
            body = _with_pkce_challenge(body, pkce_flow)
        else:
            query = URLQuery.empty()
        response = yield JSONRequest(
            method="POST",
            path=["resend"],
            body=body,
            query=query,
        )
        return parse_auth_otp_response(response)

    @handle_http_io
    def _verify_otp(self, params: VerifyOtpParams) -> HttpMethod[AuthResponse]:
        if isinstance(params, VerifyTokenHashParams):
            query = URLQuery.empty()
        else:
            query = _redirect_to_as_query(params.redirect_to)
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
            raise _handle_error_response(response)
        return AuthResponse(user=None, session=None)

    @handle_http_io
    def _update_user(
        self,
        session: Session,
        attributes: UserAttributes,
        email_redirect_to: str | None = None,
        pkce_flow: _PKCEFlow | None = None,
    ) -> HttpMethod[UserResponse]:
        """
        Updates user data, if there is a logged in user.
        """
        response = yield JSONRequest(
            method="PUT",
            path=["user"],
            body=_with_pkce_challenge(attributes, pkce_flow),
            query=_redirect_to_as_query(
                self._redirect_with_flow_id(email_redirect_to, pkce_flow)
            ),
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
                expires_at = exp
        if has_expired:
            if not refresh_token:
                raise AuthSessionMissingError
            session = yield from self.session_manager._refresh_access_token(
                refresh_token
            )
        else:
            user_response = yield from self.session_manager._get_user(access_token)
            if user_response is None:
                raise UserDoesNotExistError
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
        callback: Callable[[AuthStateChange], None],
    ) -> Subscription:
        """
        Receive a notification every time the auth state changes.

        `callback` is first called with `INITIAL_SESSION` and the session the
        client knows of, before this method returns. Call `initialize()` first
        to have a persisted session recovered by then.
        """
        return self.session_manager.subscribe(callback)

    @handle_http_io
    def _reset_password_for_email(
        self,
        email: str,
        captcha_token: str | None = None,
        redirect_to: str | None = None,
        pkce_flow: _PKCEFlow | None = None,
    ) -> HttpMethod[None]:
        """
        Sends a password reset request to an email address.
        """
        response = yield JSONRequest(
            method="POST",
            path=["recover"],
            body=_with_pkce_challenge(
                {
                    "email": email,
                    "gotrue_meta_security": {
                        "captcha_token": captcha_token,
                    },
                },
                pkce_flow,
            ),
            query=_redirect_to_as_query(
                self._redirect_with_flow_id(redirect_to, pkce_flow)
            ),
        )
        if not response.is_success:
            raise _handle_error_response(response)

    @handle_http_io
    def _get_session_from_url(
        self,
        url: str,
    ) -> HttpMethod[tuple[Session, str | None]]:
        result = URL(url)
        if not _is_implicit_grant_flow(result):
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
            raise UserDoesNotExistError
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
        pkce_flow: _PKCEFlow | None,
    ) -> URLQuery:
        if pkce_flow:
            for key, value in _pkce_challenge_params(pkce_flow.code_verifier).items():
                query = query.set(key, value)
        return query.set("provider", provider)

    @handle_http_io
    def _exchange_code_for_session(
        self, code_verifier: str | None, auth_code: str, redirect_to: str | None
    ) -> HttpMethod[AuthResponse]:
        query = _redirect_to_as_query(redirect_to).set("grant_type", "pkce")
        response = yield JSONRequest(
            method="POST",
            path=["token"],
            body={
                "auth_code": auth_code,
                "code_verifier": code_verifier
                and _strip_password_recovery_suffix(code_verifier),
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

        validate_expiration(decoded_jwt.payload.exp)
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


class AsyncSupabaseAuthClient(
    SupabaseAuthHttpClient[AsyncHttpIO, _AsyncSessionManager]
):
    def __init__(
        self,
        url: str,
        http_session: AsyncHttpSession,
        *,
        headers: Mapping[str, str] | None = None,
        storage_key: str = STORAGE_KEY,
        auto_refresh_token: bool = True,
        storage: AsyncSupportedStorage | None = None,
        flow_type: AuthFlowType = "implicit",
        append_flow_id_to_redirects: bool = False,
        request_timeout: float | None = None,
        retry: RetryPolicy | None = None,
    ) -> None:
        self.base_url = URL(url)
        supabase_headers = Headers.supabase_client_headers("supabase_auth", __version__)
        user_headers = Headers.from_mapping(headers) if headers else Headers.empty()
        default_headers = supabase_headers.update(user_headers)
        executor = AsyncHttpIO(
            session=http_session, request_timeout=request_timeout, retry=retry
        )
        self.session_manager = _AsyncSessionManager(
            base_url=self.base_url,
            executor=executor,
            default_headers=default_headers,
            storage=storage if storage is not None else AsyncMemoryStorage(),
            state_change_emitters={},
            storage_key=storage_key,
            auto_refresh_token=auto_refresh_token,
        )
        super().__init__(
            base_url=self.base_url,
            executor=executor,
            default_headers=default_headers,
            session_manager=self.session_manager,
            _jwks=JWKSet(keys=[]),
            flow_type=flow_type,
            append_flow_id_to_redirects=append_flow_id_to_redirects,
        )
        self._pkce_lock = asyncio.Lock()
        self.mfa = AsyncSupabaseAuthMFAClient(
            base_url=self.base_url,
            executor=executor,
            default_headers=default_headers,
            session_manager=self.session_manager,
        )

    async def __aenter__(self) -> Self:
        await self.executor.session.__aenter__()
        await self.session_manager.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.executor.session.__aexit__(exc_type, exc, tb)
        await self.session_manager.__aexit__(exc_type, exc, tb)

    # Initializations

    async def initialize(self, *, url: str | None = None) -> None:
        if url and _is_implicit_grant_flow(URL(url)):
            await self.initialize_from_url(url)
        else:
            await self.initialize_from_storage()

    async def initialize_from_storage(self) -> None:
        return await self.session_manager.recover_and_refresh()

    async def initialize_from_url(self, url: str) -> None:
        try:
            if _is_implicit_grant_flow(URL(url)):
                session, redirect_type = await self._get_session_from_url(url)
                await self.session_manager.save_session(session)
                self.session_manager.notify_all_subscribers(
                    AuthStateChange(AuthChangeEvent.SIGNED_IN, session)
                )
                if redirect_type == "recovery":
                    self.session_manager.notify_all_subscribers(
                        AuthStateChange(AuthChangeEvent.PASSWORD_RECOVERY, session)
                    )
        except Exception as e:
            await self.session_manager.remove_session()
            raise e

    async def _save_session_and_sign_in(self, auth_response: AuthResponse) -> None:
        if auth_response.session:
            await self.session_manager.save_session(auth_response.session)
            self.session_manager.notify_all_subscribers(
                AuthStateChange(AuthChangeEvent.SIGNED_IN, auth_response.session)
            )

    async def _store_pkce_flow(
        self, pkce_flow: _PKCEFlow, *, password_recovery: bool = False
    ) -> None:
        storage = self.session_manager.storage
        async with self._pkce_lock:
            await storage.set_item(
                self._flow_storage_key(pkce_flow.flow_id),
                self._stored_code_verifier(pkce_flow.code_verifier, password_recovery),
            )
            index, evicted = _push_flow(
                _parse_flow_index(await storage.get_item(self._flow_index_storage_key)),
                pkce_flow.flow_id,
            )
            for flow_id in evicted:
                await storage.remove_item(self._flow_storage_key(flow_id))
            await storage.set_item(self._flow_index_storage_key, json.dumps(index))

    @asynccontextmanager
    async def _removing_rejected_flow(
        self, pkce_flow: _PKCEFlow | None
    ) -> AsyncGenerator[None]:
        try:
            yield
        except SupabaseAPIError:
            if pkce_flow:
                await self._remove_pkce_flow(pkce_flow.flow_id)
            raise

    async def _start_pkce_flow(
        self, *, password_recovery: bool = False
    ) -> _PKCEFlow | None:
        pkce_flow = self._new_pkce_flow()
        if pkce_flow:
            await self._store_pkce_flow(pkce_flow, password_recovery=password_recovery)
        return pkce_flow

    async def _pending_code_verifier(
        self, flow_id: str | None
    ) -> tuple[str | None, str]:
        storage = self.session_manager.storage
        if flow_id is not None:
            verifier = (
                await storage.get_item(self._flow_storage_key(flow_id))
                if _is_valid_flow_id(flow_id)
                else None
            )
            if verifier is None:
                raise AuthPKCECodeVerifierMissingError(flow_id)
            return flow_id, verifier
        index = _parse_flow_index(await storage.get_item(self._flow_index_storage_key))
        for pending in reversed(index):
            verifier = await storage.get_item(self._flow_storage_key(pending))
            if verifier is not None:
                return pending, verifier
        verifier = await storage.get_item(self._code_verifier_storage_key)
        if verifier is None:
            raise AuthPKCECodeVerifierMissingError(None)
        return None, verifier

    async def _remove_pkce_flow(self, flow_id: str | None) -> None:
        storage = self.session_manager.storage
        if flow_id is None:
            await storage.remove_item(self._code_verifier_storage_key)
            return
        async with self._pkce_lock:
            await storage.remove_item(self._flow_storage_key(flow_id))
            index = _parse_flow_index(
                await storage.get_item(self._flow_index_storage_key)
            )
            remaining = [pending for pending in index if pending != flow_id]
            if len(remaining) == len(index):
                return
            if remaining:
                await storage.set_item(
                    self._flow_index_storage_key, json.dumps(remaining)
                )
            else:
                await storage.remove_item(self._flow_index_storage_key)

    async def _remove_all_pkce_flows(self) -> None:
        storage = self.session_manager.storage
        async with self._pkce_lock:
            index = _parse_flow_index(
                await storage.get_item(self._flow_index_storage_key)
            )
            for flow_id in index:
                await storage.remove_item(self._flow_storage_key(flow_id))
            await storage.remove_item(self._flow_index_storage_key)
            await storage.remove_item(self._code_verifier_storage_key)

    async def exchange_code_for_session(
        self,
        auth_code: str,
        *,
        flow_id: str | None = None,
        code_verifier: str | None = None,
        redirect_to: str | None = None,
    ) -> AuthResponse:
        """
        Exchanges a PKCE auth code for a session and signs the user in.

        `flow_id` names the flow that produced the code. It is returned in the
        `OAuthResponse` or `SSOResponse` that started the flow, and with
        `append_flow_id_to_redirects` it is also the `sb_flow_id` query
        parameter of the redirect URL. Pass it when several flows can be
        pending at once, such as sign-ins in two tabs. Without it, the most
        recently started flow that is still pending is used. Up to 5 flows are
        kept pending, so starting a sixth forgets the oldest.

        Pass `code_verifier` instead of `flow_id` to use a verifier you stored
        yourself.

        Raises `AuthPKCECodeVerifierMissingError`, without sending the code,
        when no verifier is stored for the flow.
        """
        if flow_id is not None and code_verifier is not None:
            raise ValueError("Pass either flow_id or code_verifier, not both")
        if code_verifier is not None:
            auth_response = await self._exchange_code_for_session(
                code_verifier, auth_code, redirect_to
            )
        else:
            pending_flow_id, verifier = await self._pending_code_verifier(flow_id)
            try:
                auth_response = await self._exchange_code_for_session(
                    verifier, auth_code, redirect_to
                )
            finally:
                await self._remove_pkce_flow(pending_flow_id)
        await self._save_session_and_sign_in(auth_response)
        return auth_response

    # Public methods

    async def sign_in_anonymously(
        self, data: JSON = None, captcha_token: str | None = None
    ) -> AuthResponse:
        """
        Creates a new anonymous user.
        """
        auth_response = await self._sign_in_anonymously(data, captcha_token)
        await self._save_session_and_sign_in(auth_response)
        return auth_response

    async def sign_up(
        self,
        credentials: SignUpWithPasswordCredentials,
    ) -> AuthResponse:
        """
        Creates a new user.
        """
        pkce_flow = (
            await self._start_pkce_flow()
            if isinstance(credentials, SignUpWithEmailAndPasswordCredentials)
            else None
        )
        async with self._removing_rejected_flow(pkce_flow):
            auth_response = await self._sign_up(credentials, pkce_flow)
        if pkce_flow and auth_response.session:
            await self._remove_pkce_flow(pkce_flow.flow_id)
        await self._save_session_and_sign_in(auth_response)
        return auth_response

    async def sign_in_with_password(
        self,
        credentials: SignInWithPasswordCredentials,
    ) -> AuthResponse:
        """
        Log in an existing user with an email or phone and password.
        """
        auth_response = await self._sign_in_with_password(credentials)
        await self._save_session_and_sign_in(auth_response)
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
        await self._save_session_and_sign_in(auth_response)
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
        oauth_response, pkce_flow = self._sign_in_with_oauth(
            provider, redirect_to, scopes, query_params
        )
        if pkce_flow:
            await self._store_pkce_flow(pkce_flow)
        return oauth_response

    async def link_identity(
        self,
        provider: Provider,
        redirect_to: str | None = None,
        scopes: str | None = None,
        query_params: dict[str, str] | None = None,
    ) -> OAuthResponse:
        session = await self.session_manager.get_session_or_raise()
        oauth_response, pkce_flow = await self._link_identity(
            session, provider, redirect_to, scopes, query_params
        )
        if pkce_flow:
            await self._store_pkce_flow(pkce_flow)
        return oauth_response

    async def get_user_identities(self) -> IdentitiesResponse:
        response = await self.get_user()
        if not response:
            raise AuthSessionMissingError
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
        pkce_flow = (
            await self._start_pkce_flow()
            if isinstance(credentials, SignInWithEmailAndPasswordlessCredentials)
            else None
        )
        async with self._removing_rejected_flow(pkce_flow):
            return await self._sign_in_with_otp(credentials, pkce_flow)

    async def resend(self, credentials: ResendCredentials) -> AuthOtpResponse:
        """
        Resends a sign-up or email change confirmation, or an SMS or phone
        change OTP.
        """
        pkce_flow = (
            await self._start_pkce_flow()
            if isinstance(credentials, ResendEmailCredentials)
            else None
        )
        async with self._removing_rejected_flow(pkce_flow):
            return await self._resend(credentials, pkce_flow)

    async def sign_in_with_sso(
        self, credentials: SignInWithSSOCredentials
    ) -> SSOResponse:
        """
        Attempts a single-sign on using an enterprise Identity Provider.
        """
        pkce_flow = await self._start_pkce_flow()
        async with self._removing_rejected_flow(pkce_flow):
            return await self._sign_in_with_sso(credentials, pkce_flow)

    async def reset_password_for_email(
        self,
        email: str,
        captcha_token: str | None = None,
        redirect_to: str | None = None,
    ) -> None:
        """
        Sends a password reset request to an email address.
        """
        pkce_flow = await self._start_pkce_flow(password_recovery=True)
        async with self._removing_rejected_flow(pkce_flow):
            await self._reset_password_for_email(
                email, captcha_token, redirect_to, pkce_flow
            )

    async def verify_otp(self, params: VerifyOtpParams) -> AuthResponse:
        """
        Log in a user given a User supplied OTP received via mobile.
        """
        auth_response = await self._verify_otp(params)
        await self._save_session_and_sign_in(auth_response)
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
        pkce_flow = (
            await self._start_pkce_flow() if attributes.email is not None else None
        )
        async with self._removing_rejected_flow(pkce_flow):
            user_response = await self._update_user(
                session, attributes, email_redirect_to, pkce_flow
            )
        await self.session_manager.save_session(session)
        self.session_manager.notify_all_subscribers(
            AuthStateChange(AuthChangeEvent.USER_UPDATED, session)
        )
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
            event = (
                AuthChangeEvent.SIGNED_IN
                if auth_response.session.access_token == access_token
                else AuthChangeEvent.TOKEN_REFRESHED
            )
            self.session_manager.notify_all_subscribers(
                AuthStateChange(event, auth_response.session)
            )
        return auth_response

    async def refresh_session(self, refresh_token: str | None = None) -> AuthResponse:
        """
        Returns a new session, regardless of expiry status.

        Takes in an optional current session. If not passed in, then refreshSession()
        will attempt to retrieve it from getSession(). If the current session's
        refresh token is invalid, an error will be thrown.
        """
        session = (
            await self.session_manager.call_refresh_token(refresh_token)
            if refresh_token
            else await self.session_manager.refresh_session()
        )
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
            await self._remove_all_pkce_flows()
            self.session_manager.notify_all_subscribers(
                AuthStateChange(
                    AuthChangeEvent.SIGNED_OUT,
                    sign_out_reason=SignOutReason.USER_INITIATED,
                )
            )

    @override
    def on_auth_state_change(
        self,
        callback: Callable[[AuthStateChange], None],
    ) -> Subscription:
        """
        Receive a notification every time the auth state changes.

        `callback` is first called with `INITIAL_SESSION` and the session the
        client knows of, before this method returns. Call `initialize()` first
        to have a persisted session recovered by then.
        """
        return self.session_manager.subscribe(callback)

    async def get_claims(
        self, jwt: str | None = None, jwks: JWKSet | None = None
    ) -> ClaimsResponse | None:
        if not jwt:
            session = await self.get_session()
            if not session:
                return None
            jwt = session.access_token
        return await self._get_claims(jwt, jwks)


class SyncSupabaseAuthClient(SupabaseAuthHttpClient[SyncHttpIO, _SyncSessionManager]):
    def __init__(
        self,
        url: str,
        http_session: HttpSession,
        *,
        headers: Mapping[str, str] | None = None,
        storage_key: str = STORAGE_KEY,
        auto_refresh_token: bool = True,
        storage: SyncSupportedStorage | None = None,
        flow_type: AuthFlowType = "implicit",
        append_flow_id_to_redirects: bool = False,
        request_timeout: float | None = None,
        retry: RetryPolicy | None = None,
    ) -> None:
        self.base_url = URL(url)
        supabase_headers = Headers.supabase_client_headers("supabase_auth", __version__)
        user_headers = Headers.from_mapping(headers) if headers else Headers.empty()
        default_headers = supabase_headers.update(user_headers)
        executor = SyncHttpIO(
            session=http_session, request_timeout=request_timeout, retry=retry
        )
        self.session_manager = _SyncSessionManager(
            base_url=self.base_url,
            executor=executor,
            default_headers=default_headers,
            storage=storage if storage is not None else SyncMemoryStorage(),
            state_change_emitters={},
            storage_key=storage_key,
            auto_refresh_token=auto_refresh_token,
        )
        super().__init__(
            base_url=self.base_url,
            executor=executor,
            default_headers=default_headers,
            session_manager=self.session_manager,
            _jwks=JWKSet(keys=[]),
            flow_type=flow_type,
            append_flow_id_to_redirects=append_flow_id_to_redirects,
        )
        self._pkce_lock = threading.Lock()
        self.mfa = SyncSupabaseAuthMFAClient(
            base_url=self.base_url,
            executor=executor,
            default_headers=default_headers,
            session_manager=self.session_manager,
        )

    def __enter__(self) -> Self:
        self.executor.session.__enter__()
        self.session_manager.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.executor.session.__exit__(exc_type, exc, tb)
        self.session_manager.__exit__(exc_type, exc, tb)

    # Initializations

    def initialize(self, *, url: str | None = None) -> None:
        if url and _is_implicit_grant_flow(URL(url)):
            self.initialize_from_url(url)
        else:
            self.initialize_from_storage()

    def initialize_from_storage(self) -> None:
        return self.session_manager.recover_and_refresh()

    def initialize_from_url(self, url: str) -> None:
        try:
            if _is_implicit_grant_flow(URL(url)):
                session, redirect_type = self._get_session_from_url(url)
                self.session_manager.save_session(session)
                self.session_manager.notify_all_subscribers(
                    AuthStateChange(AuthChangeEvent.SIGNED_IN, session)
                )
                if redirect_type == "recovery":
                    self.session_manager.notify_all_subscribers(
                        AuthStateChange(AuthChangeEvent.PASSWORD_RECOVERY, session)
                    )
        except Exception as e:
            self.session_manager.remove_session()
            raise e

    def _save_session_and_sign_in(self, auth_response: AuthResponse) -> None:
        if auth_response.session:
            self.session_manager.save_session(auth_response.session)
            self.session_manager.notify_all_subscribers(
                AuthStateChange(AuthChangeEvent.SIGNED_IN, auth_response.session)
            )

    def _store_pkce_flow(
        self, pkce_flow: _PKCEFlow, *, password_recovery: bool = False
    ) -> None:
        storage = self.session_manager.storage
        with self._pkce_lock:
            storage.set_item(
                self._flow_storage_key(pkce_flow.flow_id),
                self._stored_code_verifier(pkce_flow.code_verifier, password_recovery),
            )
            index, evicted = _push_flow(
                _parse_flow_index(storage.get_item(self._flow_index_storage_key)),
                pkce_flow.flow_id,
            )
            for flow_id in evicted:
                storage.remove_item(self._flow_storage_key(flow_id))
            storage.set_item(self._flow_index_storage_key, json.dumps(index))

    @contextmanager
    def _removing_rejected_flow(self, pkce_flow: _PKCEFlow | None) -> Generator[None]:
        try:
            yield
        except SupabaseAPIError:
            if pkce_flow:
                self._remove_pkce_flow(pkce_flow.flow_id)
            raise

    def _start_pkce_flow(self, *, password_recovery: bool = False) -> _PKCEFlow | None:
        pkce_flow = self._new_pkce_flow()
        if pkce_flow:
            self._store_pkce_flow(pkce_flow, password_recovery=password_recovery)
        return pkce_flow

    def _pending_code_verifier(self, flow_id: str | None) -> tuple[str | None, str]:
        storage = self.session_manager.storage
        if flow_id is not None:
            verifier = (
                storage.get_item(self._flow_storage_key(flow_id))
                if _is_valid_flow_id(flow_id)
                else None
            )
            if verifier is None:
                raise AuthPKCECodeVerifierMissingError(flow_id)
            return flow_id, verifier
        index = _parse_flow_index(storage.get_item(self._flow_index_storage_key))
        for pending in reversed(index):
            verifier = storage.get_item(self._flow_storage_key(pending))
            if verifier is not None:
                return pending, verifier
        verifier = storage.get_item(self._code_verifier_storage_key)
        if verifier is None:
            raise AuthPKCECodeVerifierMissingError(None)
        return None, verifier

    def _remove_pkce_flow(self, flow_id: str | None) -> None:
        storage = self.session_manager.storage
        if flow_id is None:
            storage.remove_item(self._code_verifier_storage_key)
            return
        with self._pkce_lock:
            storage.remove_item(self._flow_storage_key(flow_id))
            index = _parse_flow_index(storage.get_item(self._flow_index_storage_key))
            remaining = [pending for pending in index if pending != flow_id]
            if len(remaining) == len(index):
                return
            if remaining:
                storage.set_item(self._flow_index_storage_key, json.dumps(remaining))
            else:
                storage.remove_item(self._flow_index_storage_key)

    def _remove_all_pkce_flows(self) -> None:
        storage = self.session_manager.storage
        with self._pkce_lock:
            index = _parse_flow_index(storage.get_item(self._flow_index_storage_key))
            for flow_id in index:
                storage.remove_item(self._flow_storage_key(flow_id))
            storage.remove_item(self._flow_index_storage_key)
            storage.remove_item(self._code_verifier_storage_key)

    def exchange_code_for_session(
        self,
        auth_code: str,
        *,
        flow_id: str | None = None,
        code_verifier: str | None = None,
        redirect_to: str | None = None,
    ) -> AuthResponse:
        """
        Exchanges a PKCE auth code for a session and signs the user in.

        `flow_id` names the flow that produced the code. It is returned in the
        `OAuthResponse` or `SSOResponse` that started the flow, and with
        `append_flow_id_to_redirects` it is also the `sb_flow_id` query
        parameter of the redirect URL. Pass it when several flows can be
        pending at once, such as sign-ins in two tabs. Without it, the most
        recently started flow that is still pending is used. Up to 5 flows are
        kept pending, so starting a sixth forgets the oldest.

        Pass `code_verifier` instead of `flow_id` to use a verifier you stored
        yourself.

        Raises `AuthPKCECodeVerifierMissingError`, without sending the code,
        when no verifier is stored for the flow.
        """
        if flow_id is not None and code_verifier is not None:
            raise ValueError("Pass either flow_id or code_verifier, not both")
        if code_verifier is not None:
            auth_response = self._exchange_code_for_session(
                code_verifier, auth_code, redirect_to
            )
        else:
            pending_flow_id, verifier = self._pending_code_verifier(flow_id)
            try:
                auth_response = self._exchange_code_for_session(
                    verifier, auth_code, redirect_to
                )
            finally:
                self._remove_pkce_flow(pending_flow_id)
        self._save_session_and_sign_in(auth_response)
        return auth_response

    # Public methods

    def sign_in_anonymously(
        self, data: JSON = None, captcha_token: str | None = None
    ) -> AuthResponse:
        """
        Creates a new anonymous user.
        """
        auth_response = self._sign_in_anonymously(data, captcha_token)
        self._save_session_and_sign_in(auth_response)
        return auth_response

    def sign_up(
        self,
        credentials: SignUpWithPasswordCredentials,
    ) -> AuthResponse:
        """
        Creates a new user.
        """
        pkce_flow = (
            self._start_pkce_flow()
            if isinstance(credentials, SignUpWithEmailAndPasswordCredentials)
            else None
        )
        with self._removing_rejected_flow(pkce_flow):
            auth_response = self._sign_up(credentials, pkce_flow)
        if pkce_flow and auth_response.session:
            self._remove_pkce_flow(pkce_flow.flow_id)
        self._save_session_and_sign_in(auth_response)
        return auth_response

    def sign_in_with_password(
        self,
        credentials: SignInWithPasswordCredentials,
    ) -> AuthResponse:
        """
        Log in an existing user with an email or phone and password.
        """
        auth_response = self._sign_in_with_password(credentials)
        self._save_session_and_sign_in(auth_response)
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
        self._save_session_and_sign_in(auth_response)
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
        oauth_response, pkce_flow = self._sign_in_with_oauth(
            provider, redirect_to, scopes, query_params
        )
        if pkce_flow:
            self._store_pkce_flow(pkce_flow)
        return oauth_response

    def link_identity(
        self,
        provider: Provider,
        redirect_to: str | None = None,
        scopes: str | None = None,
        query_params: dict[str, str] | None = None,
    ) -> OAuthResponse:
        session = self.session_manager.get_session_or_raise()
        oauth_response, pkce_flow = self._link_identity(
            session, provider, redirect_to, scopes, query_params
        )
        if pkce_flow:
            self._store_pkce_flow(pkce_flow)
        return oauth_response

    def get_user_identities(self) -> IdentitiesResponse:
        response = self.get_user()
        if not response:
            raise AuthSessionMissingError
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
        pkce_flow = (
            self._start_pkce_flow()
            if isinstance(credentials, SignInWithEmailAndPasswordlessCredentials)
            else None
        )
        with self._removing_rejected_flow(pkce_flow):
            return self._sign_in_with_otp(credentials, pkce_flow)

    def resend(self, credentials: ResendCredentials) -> AuthOtpResponse:
        """
        Resends a sign-up or email change confirmation, or an SMS or phone
        change OTP.
        """
        pkce_flow = (
            self._start_pkce_flow()
            if isinstance(credentials, ResendEmailCredentials)
            else None
        )
        with self._removing_rejected_flow(pkce_flow):
            return self._resend(credentials, pkce_flow)

    def sign_in_with_sso(self, credentials: SignInWithSSOCredentials) -> SSOResponse:
        """
        Attempts a single-sign on using an enterprise Identity Provider.
        """
        pkce_flow = self._start_pkce_flow()
        with self._removing_rejected_flow(pkce_flow):
            return self._sign_in_with_sso(credentials, pkce_flow)

    def reset_password_for_email(
        self,
        email: str,
        captcha_token: str | None = None,
        redirect_to: str | None = None,
    ) -> None:
        """
        Sends a password reset request to an email address.
        """
        pkce_flow = self._start_pkce_flow(password_recovery=True)
        with self._removing_rejected_flow(pkce_flow):
            self._reset_password_for_email(email, captcha_token, redirect_to, pkce_flow)

    def verify_otp(self, params: VerifyOtpParams) -> AuthResponse:
        """
        Log in a user given a User supplied OTP received via mobile.
        """
        auth_response = self._verify_otp(params)
        self._save_session_and_sign_in(auth_response)
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
        pkce_flow = self._start_pkce_flow() if attributes.email is not None else None
        with self._removing_rejected_flow(pkce_flow):
            user_response = self._update_user(
                session, attributes, email_redirect_to, pkce_flow
            )
        self.session_manager.save_session(session)
        self.session_manager.notify_all_subscribers(
            AuthStateChange(AuthChangeEvent.USER_UPDATED, session)
        )
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
            event = (
                AuthChangeEvent.SIGNED_IN
                if auth_response.session.access_token == access_token
                else AuthChangeEvent.TOKEN_REFRESHED
            )
            self.session_manager.notify_all_subscribers(
                AuthStateChange(event, auth_response.session)
            )
        return auth_response

    def refresh_session(self, refresh_token: str | None = None) -> AuthResponse:
        """
        Returns a new session, regardless of expiry status.

        Takes in an optional current session. If not passed in, then refreshSession()
        will attempt to retrieve it from getSession(). If the current session's
        refresh token is invalid, an error will be thrown.
        """
        session = (
            self.session_manager.call_refresh_token(refresh_token)
            if refresh_token
            else self.session_manager.refresh_session()
        )
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
            self._remove_all_pkce_flows()
            self.session_manager.notify_all_subscribers(
                AuthStateChange(
                    AuthChangeEvent.SIGNED_OUT,
                    sign_out_reason=SignOutReason.USER_INITIATED,
                )
            )

    @override
    def on_auth_state_change(
        self,
        callback: Callable[[AuthStateChange], None],
    ) -> Subscription:
        """
        Receive a notification every time the auth state changes.

        `callback` is first called with `INITIAL_SESSION` and the session the
        client knows of, before this method returns. Call `initialize()` first
        to have a persisted session recovered by then.
        """
        return self.session_manager.subscribe(callback)

    def get_claims(
        self, jwt: str | None = None, jwks: JWKSet | None = None
    ) -> ClaimsResponse | None:
        if not jwt:
            session = self.get_session()
            if not session:
                return None
            jwt = session.access_token
        return self._get_claims(jwt, jwks)
