from __future__ import annotations

from datetime import datetime
from time import time
from typing import Callable, List, Mapping

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    TypeAdapter,
    model_validator,
)
from pydantic.dataclasses import dataclass
from supabase_utils.http.headers import Headers
from supabase_utils.types import JSON

try:
    # > 2
    from pydantic import model_validator

    model_validator_v1_v2_compat = model_validator(mode="before")
except ImportError:
    # < 2
    from pydantic import root_validator

    model_validator_v1_v2_compat = root_validator  # type: ignore

from typing_extensions import Literal, TypedDict

Provider = Literal[
    "apple",
    "azure",
    "bitbucket",
    "discord",
    "facebook",
    "figma",
    "fly",
    "github",
    "gitlab",
    "google",
    "kakao",
    "keycloak",
    "linkedin",
    "linkedin_oidc",
    "notion",
    "slack",
    "slack_oidc",
    "spotify",
    "twitch",
    "twitter",  # Uses OAuth 1.0a
    "x",  # Uses OAuth 2.0
    "workos",
    "zoom",
]

EmailOtpType = Literal[
    "signup", "invite", "magiclink", "recovery", "email_change", "email"
]

AuthChangeEventMFA = Literal["MFA_CHALLENGE_VERIFIED"]

AuthFlowType = Literal["pkce", "implicit"]

AuthChangeEvent = Literal[
    "PASSWORD_RECOVERY",
    "SIGNED_IN",
    "SIGNED_OUT",
    "TOKEN_REFRESHED",
    "USER_UPDATED",
    "USER_DELETED",
    AuthChangeEventMFA,
]


class AMREntry(BaseModel):
    """
    An authentication methord reference (AMR) entry.

    An entry designates what method was used by the user to verify their
    identity and at what time.
    """

    method: Literal["password", "otp", "oauth", "mfa/totp"] | str
    """
    Authentication method name.
    """
    timestamp: int
    """
    Timestamp when the method was successfully used. Represents number of
    seconds since 1st January 1970 (UNIX epoch) in UTC.
    """


class AMREntryDict(TypedDict):
    timestamp: int
    method: Literal["password", "otp", "oauth", "mfa/totp"] | str


class AuthResponse(BaseModel):
    user: User | None = None
    session: Session | None = None


class AuthOtpResponse(BaseModel):
    user: None = None
    session: None = None
    message_id: str | None = None


class OAuthResponse(BaseModel):
    provider: Provider
    url: str


class SSOResponse(BaseModel):
    url: str


class LinkIdentityResponse(BaseModel):
    url: str


class IdentitiesResponse(BaseModel):
    identities: list[UserIdentity]


class UserList(BaseModel):
    users: list[User]


class UserResponse(BaseModel):
    user: User


class Session(BaseModel):
    provider_token: str | None = None
    """
    The oauth provider token. If present, this can be used to make external API
    requests to the oauth provider used.
    """
    provider_refresh_token: str | None = None
    """
    The oauth provider refresh token. If present, this can be used to refresh
    the provider_token via the oauth provider's API.

    Not all oauth providers return a provider refresh token. If the
    provider_refresh_token is missing, please refer to the oauth provider's
    documentation for information on how to obtain the provider refresh token.
    """
    access_token: str
    refresh_token: str
    expires_in: int
    """
    The number of seconds until the token expires (since it was issued).
    Returned when a login is confirmed.
    """
    expires_at: int | None = None
    """
    A timestamp of when the token will expire. Returned when a login is confirmed.
    """
    token_type: str
    user: User

    @model_validator(mode="after")
    def validator(self) -> Session:
        if self.expires_in and not self.expires_at:
            self.expires_at = round(time()) + self.expires_in
        return self

    def encode_access_token(self) -> Headers:
        return Headers.from_mapping({"Authorization": f"Bearer {self.access_token}"})


class UserIdentity(BaseModel):
    id: str
    identity_id: str
    user_id: str
    identity_data: dict[str, JSON]
    provider: str
    created_at: datetime
    last_sign_in_at: datetime | None = None
    updated_at: datetime | None = None


class Factor(BaseModel):
    """
    A MFA factor.
    """

    id: str
    """
    ID of the factor.
    """
    friendly_name: str | None = None
    """
    Friendly name of the factor, useful to disambiguate between multiple factors.
    """
    factor_type: Literal["totp", "phone"] | str
    """
    Type of factor. Only `totp` supported with this version but may change in
    future versions.
    """
    status: Literal["verified", "unverified"]
    """
    Factor's status.
    """
    created_at: datetime
    updated_at: datetime


class User(BaseModel):
    id: str
    user_metadata: Mapping[str, JSON]
    app_metadata: Mapping[str, JSON]
    aud: str
    confirmation_sent_at: datetime | None = None
    recovery_sent_at: datetime | None = None
    email_change_sent_at: datetime | None = None
    new_email: str | None = None
    new_phone: str | None = None
    invited_at: datetime | None = None
    action_link: str | None = None
    email: str | None = None
    phone: str | None = None
    created_at: datetime
    confirmed_at: datetime | None = None
    email_confirmed_at: datetime | None = None
    phone_confirmed_at: datetime | None = None
    last_sign_in_at: datetime | None = None
    role: str | None = None
    updated_at: datetime | None = None
    identities: list[UserIdentity] | None = None
    is_anonymous: bool = False
    is_sso_user: bool = False
    factors: list[Factor] | None = None
    deleted_at: str | None = None
    banned_until: str | None = None


class UserAttributes(BaseModel):
    email: str | None = None
    phone: str | None = None
    password: str | None = None
    data: JSON = None
    nonce: str | None = None


class AdminUserAttributes(UserAttributes):
    user_metadata: Mapping[str, JSON] | None = None
    app_metadata: Mapping[str, JSON] | None = None
    email_confirm: bool | None = None
    phone_confirm: bool | None = None
    ban_duration: str | None = None
    role: str | None = None
    """
    The `role` claim set in the user's access token JWT.

    When a user signs up, this role is set to `authenticated` by default. You should only modify the `role` if you need to provision several levels of admin access that have different permissions on individual columns in your database.

    Setting this role to `service_role` is not recommended as it grants the user admin privileges.
    """
    password_hash: str | None = None
    """
    The `password_hash` for the user's password.

    Allows you to specify a password hash for the user. This is useful for migrating a user's password hash from another service.

    Supports bcrypt and argon2 password hashes.
    """
    id: str | None = None
    """
    The `id` for the user.

    Allows you to overwrite the default `id` set for the user.
    """


class Subscription(BaseModel):
    id: str
    """
    The subscriber UUID. This will be set by the client.
    """
    callback: Callable[[AuthChangeEvent, Session | None], None]
    """
    The function to call every time there is an event.
    """
    unsubscribe: Callable[[], None]
    """
    Call this to remove the listener.
    """


class CaptchaToken(BaseModel):
    captcha_token: str | None


class WithCaptchaToken(BaseModel):
    gotrue_meta_security: CaptchaToken


class SignUpWithEmailAndPasswordBody(WithCaptchaToken):
    email: str
    password: str
    data: JSON | None = None


@dataclass
class SignUpWithEmailAndPasswordCredentials:
    body: SignUpWithEmailAndPasswordBody
    redirect_to: str | None = None


class SignUpWithPhoneAndPasswordBody(WithCaptchaToken):
    phone: str
    password: str
    data: JSON | None = None
    channel: Literal["sms", "whatsapp"] = "sms"


@dataclass
class SignUpWithPhoneAndPasswordCredentials:
    body: SignUpWithPhoneAndPasswordBody


class SignUpWithPassword:
    @staticmethod
    def phone(
        phone: str,
        password: str,
        data: JSON | None = None,
        channel: Literal["sms", "whatsapp"] = "sms",
        captcha_token: str | None = None,
    ) -> SignUpWithPhoneAndPasswordCredentials:
        body = SignUpWithPhoneAndPasswordBody(
            phone=phone,
            password=password,
            data=data,
            channel=channel,
            gotrue_meta_security=CaptchaToken(captcha_token=captcha_token),
        )
        return SignUpWithPhoneAndPasswordCredentials(body=body)

    @staticmethod
    def email(
        email: str,
        password: str,
        data: JSON | None = None,
        redirect_to: str | None = None,
        captcha_token: str | None = None,
    ) -> SignUpWithEmailAndPasswordCredentials:
        body = SignUpWithEmailAndPasswordBody(
            email=email,
            password=password,
            data=data,
            gotrue_meta_security=CaptchaToken(captcha_token=captcha_token),
        )
        return SignUpWithEmailAndPasswordCredentials(body=body, redirect_to=redirect_to)


SignUpWithPasswordCredentials = (
    SignUpWithEmailAndPasswordCredentials | SignUpWithPhoneAndPasswordCredentials
)


class SignInWithEmailAndPasswordCredentials(WithCaptchaToken):
    email: str
    password: str


class SignInWithPhoneAndPasswordCredentials(WithCaptchaToken):
    phone: str
    password: str


SignInWithPasswordCredentials = (
    SignInWithEmailAndPasswordCredentials | SignInWithPhoneAndPasswordCredentials
)


class SignInWithPassword:
    @staticmethod
    def phone(
        phone: str, password: str, captcha_token: str | None = None
    ) -> SignInWithPhoneAndPasswordCredentials:
        return SignInWithPhoneAndPasswordCredentials(
            phone=phone,
            password=password,
            gotrue_meta_security=CaptchaToken(captcha_token=captcha_token),
        )

    @staticmethod
    def email(
        email: str, password: str, captcha_token: str | None = None
    ) -> SignInWithEmailAndPasswordCredentials:
        return SignInWithEmailAndPasswordCredentials(
            email=email,
            password=password,
            gotrue_meta_security=CaptchaToken(captcha_token=captcha_token),
        )


class SignInWithEmailAndPasswordlessBody(WithCaptchaToken):
    email: str
    data: JSON = None
    create_user: bool = True


class SignInWithPhoneAndPasswordlessBody(WithCaptchaToken):
    phone: str
    data: JSON = None
    create_user: bool = True
    channel: Literal["sms", "whatsapp"] = "sms"


@dataclass
class SignInWithEmailAndPasswordlessCredentials:
    body: SignInWithEmailAndPasswordlessBody
    email_redirect_to: str | None = None


@dataclass
class SignInWithPhoneAndPasswordlessCredentials:
    body: SignInWithPhoneAndPasswordlessBody


SignInWithPasswordlessCredentials = (
    SignInWithEmailAndPasswordlessCredentials
    | SignInWithPhoneAndPasswordlessCredentials
)


class SignInWithPasswordless:
    @staticmethod
    def email(
        email: str,
        data: JSON = None,
        should_create_user: bool = True,
        email_redirect_to: str | None = None,
        captcha_token: str | None = None,
    ) -> SignInWithPasswordlessCredentials:
        body = SignInWithEmailAndPasswordlessBody(
            email=email,
            data=data,
            create_user=should_create_user,
            gotrue_meta_security=CaptchaToken(captcha_token=captcha_token),
        )
        return SignInWithEmailAndPasswordlessCredentials(
            body=body, email_redirect_to=email_redirect_to
        )

    @staticmethod
    def phone(
        phone: str,
        data: JSON = None,
        should_create_user: bool = True,
        channel: Literal["sms", "whatsapp"] = "sms",
        captcha_token: str | None = None,
    ) -> SignInWithPasswordlessCredentials:
        body = SignInWithPhoneAndPasswordlessBody(
            phone=phone,
            data=data,
            create_user=should_create_user,
            gotrue_meta_security=CaptchaToken(captcha_token=captcha_token),
            channel=channel,
        )
        return SignInWithPhoneAndPasswordlessCredentials(body=body)


class ResendEmailBody(WithCaptchaToken):
    type: Literal["signup", "email_change"]
    email: str


@dataclass
class ResendEmailCredentials:
    body: ResendEmailBody
    email_redirect_to: str | None = None


class ResendPhoneBody(WithCaptchaToken):
    type: Literal["sms", "phone_change"]
    phone: str


@dataclass
class ResendPhoneCredentials:
    body: ResendPhoneBody


ResendCredentials = ResendEmailCredentials | ResendPhoneCredentials


class Resend:
    @staticmethod
    def email(
        email: str,
        type: Literal["signup", "email_change"],
        email_redirect_to: str | None = None,
        captcha_token: str | None = None,
    ) -> ResendCredentials:
        return ResendEmailCredentials(
            body=ResendEmailBody(
                email=email,
                type=type,
                gotrue_meta_security=CaptchaToken(captcha_token=captcha_token),
            ),
            email_redirect_to=email_redirect_to,
        )

    @staticmethod
    def phone(
        phone: str,
        type: Literal["sms", "phone_change"],
        captcha_token: str | None = None,
    ) -> ResendCredentials:
        return ResendPhoneCredentials(
            body=ResendPhoneBody(
                phone=phone,
                type=type,
                gotrue_meta_security=CaptchaToken(captcha_token=captcha_token),
            ),
        )


class SignInWithSSOProvider(WithCaptchaToken):
    provider_id: str
    redirect_to: str | None = None
    skip_http_redirect: bool = True


class SignInWithSSODomain(WithCaptchaToken):
    domain: str
    redirect_to: str | None = None
    skip_http_redirect: bool = True


SignInWithSSOCredentials = SignInWithSSODomain | SignInWithSSOProvider


class SignInWithSSO:
    @staticmethod
    def domain(
        domain: str,
        redirect_to: str | None = None,
        skip_http_redirect: bool = True,
        captcha_token: str | None = None,
    ) -> SignInWithSSOCredentials:
        return SignInWithSSODomain(
            domain=domain,
            redirect_to=redirect_to,
            skip_http_redirect=skip_http_redirect,
            gotrue_meta_security=CaptchaToken(captcha_token=captcha_token),
        )

    @staticmethod
    def provider_id(
        provider_id: str,
        redirect_to: str | None = None,
        skip_http_redirect: bool = True,
        captcha_token: str | None = None,
    ) -> SignInWithSSOCredentials:
        return SignInWithSSOProvider(
            provider_id=provider_id,
            redirect_to=redirect_to,
            skip_http_redirect=skip_http_redirect,
            gotrue_meta_security=CaptchaToken(captcha_token=captcha_token),
        )


class VerifyEmailOtpBody(WithCaptchaToken):
    email: str
    token: str
    type: EmailOtpType


@dataclass
class VerifyEmailOtpParams:
    body: VerifyEmailOtpBody
    redirect_to: str | None = None


class VerifyMobileOtpBody(WithCaptchaToken):
    phone: str
    token: str
    type: Literal[
        "sms",
        "phone_change",
    ]


@dataclass
class VerifyMobileOtpParams:
    body: VerifyMobileOtpBody
    redirect_to: str | None = None


class VerifyTokenHashBody(BaseModel):
    token_hash: str
    type: EmailOtpType


@dataclass
class VerifyTokenHashParams:
    body: VerifyTokenHashBody


VerifyOtpParams = VerifyEmailOtpParams | VerifyMobileOtpParams | VerifyTokenHashParams


class VerifyOtp:
    @staticmethod
    def email(
        email: str,
        token: str,
        type: EmailOtpType,
        redirect_to: str | None = None,
        captcha_token: str | None = None,
    ) -> VerifyOtpParams:
        body = VerifyEmailOtpBody(
            email=email,
            token=token,
            type=type,
            gotrue_meta_security=CaptchaToken(captcha_token=captcha_token),
        )
        return VerifyEmailOtpParams(body=body, redirect_to=redirect_to)

    @staticmethod
    def mobile(
        phone: str,
        token: str,
        type: Literal["sms", "phone_change"],
        redirect_to: str | None = None,
        captcha_token: str | None = None,
    ) -> VerifyOtpParams:
        body = VerifyMobileOtpBody(
            phone=phone,
            token=token,
            type=type,
            gotrue_meta_security=CaptchaToken(captcha_token=captcha_token),
        )
        return VerifyMobileOtpParams(body=body, redirect_to=redirect_to)

    @staticmethod
    def token_hash(token_hash: str, type: EmailOtpType) -> VerifyOtpParams:
        body = VerifyTokenHashBody(
            token_hash=token_hash,
            type=type,
        )
        return VerifyTokenHashParams(body=body)


GenerateLinkType = Literal[
    "signup",
    "invite",
    "magiclink",
    "recovery",
    "email_change_current",
    "email_change_new",
]


class GenerateLinkBody(BaseModel):
    type: GenerateLinkType
    email: str
    password: str | None = None
    new_email: str | None = None
    data: JSON = None


class GenerateLinkParams(BaseModel):
    body: GenerateLinkBody
    redirect_to: str | None = None

    @staticmethod
    def sign_up(
        email: str, password: str, data: JSON = None, redirect_to: str | None = None
    ) -> GenerateLinkParams:
        return GenerateLinkParams(
            body=GenerateLinkBody(
                type="signup",
                email=email,
                password=password,
                data=data,
            ),
            redirect_to=redirect_to,
        )

    @staticmethod
    def invite(
        email: str, data: JSON = None, redirect_to: str | None = None
    ) -> GenerateLinkParams:
        return GenerateLinkParams(
            body=GenerateLinkBody(
                type="invite",
                email=email,
                data=data,
            ),
            redirect_to=redirect_to,
        )

    @staticmethod
    def magiclink(
        email: str, data: JSON = None, redirect_to: str | None = None
    ) -> GenerateLinkParams:
        return GenerateLinkParams(
            body=GenerateLinkBody(
                type="magiclink",
                email=email,
                data=data,
            ),
            redirect_to=redirect_to,
        )

    @staticmethod
    def recovery(email: str, redirect_to: str | None = None) -> GenerateLinkParams:
        return GenerateLinkParams(
            body=GenerateLinkBody(
                type="recovery",
                email=email,
            ),
            redirect_to=redirect_to,
        )

    @staticmethod
    def email_change_current(
        email: str, new_email: str, redirect_to: str | None = None
    ) -> GenerateLinkParams:
        return GenerateLinkParams(
            body=GenerateLinkBody(
                type="email_change_current",
                email=email,
                new_email=new_email,
            ),
            redirect_to=redirect_to,
        )

    @staticmethod
    def email_change_new(
        email: str, new_email: str, redirect_to: str | None = None
    ) -> GenerateLinkParams:
        return GenerateLinkParams(
            body=GenerateLinkBody(
                type="email_change_new",
                email=email,
                new_email=new_email,
            ),
            redirect_to=redirect_to,
        )


class MFAEnrollTOTPParams(BaseModel):
    factor_type: Literal["totp"]
    issuer: str | None = None
    friendly_name: str | None = None


class MFAEnrollPhoneParams(BaseModel):
    factor_type: Literal["phone"]
    phone: str
    friendly_name: str | None = None


class MFAEnroll:
    @staticmethod
    def totp(
        issuer: str | None = None, friendly_name: str | None = None
    ) -> MFAEnrollParams:
        return MFAEnrollTOTPParams(
            factor_type="totp",
            issuer=issuer,
            friendly_name=friendly_name,
        )

    @staticmethod
    def phone(phone: str, friendly_name: str | None = None) -> MFAEnrollParams:
        return MFAEnrollPhoneParams(
            factor_type="phone",
            phone=phone,
            friendly_name=friendly_name,
        )


MFAEnrollParams = MFAEnrollPhoneParams | MFAEnrollTOTPParams


class AuthMFAVerifyResponse(BaseModel):
    access_token: str
    """
    New access token (JWT) after successful verification.
    """
    token_type: str
    """
    Type of token, typically `Bearer`.
    """
    expires_in: int
    """
    Number of seconds in which the access token will expire.
    """
    refresh_token: str
    """
    Refresh token you can use to obtain new access tokens when expired.
    """
    user: User
    """
    Updated user profile.
    """


class AuthMFAEnrollResponseTotp(BaseModel):
    qr_code: str
    """
    Contains a QR code encoding the authenticator URI. You can
    convert it to a URL by prepending `data:image/svg+xml;utf-8,` to
    the value. Avoid logging this value to the console.
    """
    secret: str
    """
    The TOTP secret (also encoded in the QR code). Show this secret
    in a password-style field to the user, in case they are unable to
    scan the QR code. Avoid logging this value to the console.
    """
    uri: str
    """
    The authenticator URI encoded within the QR code, should you need
    to use it. Avoid loggin this value to the console.
    """


class AuthMFAEnrollResponse(BaseModel):
    id: str
    """
    ID of the factor that was just enrolled (in an unverified state).
    """
    type: Literal["totp", "phone"]
    """
    Type of MFA factor. Only `totp` supported for now.
    """
    totp: AuthMFAEnrollResponseTotp | None = None
    """
    TOTP enrollment information.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    friendly_name: str
    """
    Friendly name of the factor, useful for distinguishing between factors
    """
    phone: str | None = None
    """
    Phone number of the MFA factor in E.164 format. Used to send messages
    """

    @model_validator(mode="after")
    def validate_phone_required_for_phone_type(self) -> AuthMFAEnrollResponse:
        if self.type == "phone" and not self.phone:
            raise ValueError("phone is required when type is 'phone'")
        return self


class AuthMFAUnenrollResponse(BaseModel):
    id: str
    """
    ID of the factor that was successfully unenrolled.
    """


class AuthMFAChallengeResponse(BaseModel):
    id: str
    """
    ID of the newly created challenge.
    """
    expires_at: int
    """
    Timestamp in UNIX seconds when this challenge will no longer be usable.
    """
    factor_type: Literal["totp", "phone"] | None = Field(
        validation_alias="type", default=None
    )
    """
    Factor Type which generated the challenge
    """


class AuthMFAListFactorsResponse(BaseModel):
    all: list[Factor]
    """
    All available factors (verified and unverified).
    """
    totp: list[Factor]
    """
    Only verified TOTP factors. (A subset of `all`.)
    """
    phone: list[Factor]
    """
    Only verified Phone factors. (A subset of `all`.)
    """


AuthenticatorAssuranceLevels = Literal["aal1", "aal2"]


class AuthMFAGetAuthenticatorAssuranceLevelResponse(BaseModel):
    current_level: AuthenticatorAssuranceLevels | None = None
    """
    Current AAL level of the session.
    """
    next_level: AuthenticatorAssuranceLevels | None = None
    """
    Next possible AAL level for the session. If the next level is higher
    than the current one, the user should go through MFA.
    """
    current_authentication_methods: list[AMREntry]
    """
    A list of all authentication methods attached to this session. Use
    the information here to detect the last time a user verified a
    factor, for example if implementing a step-up scenario.
    """


class AuthMFAAdminDeleteFactorResponse(BaseModel):
    id: str
    """
    ID of the factor that was successfully deleted.
    """


AuthMFAAdminListFactorsResponse = List[Factor]

AuthMFAAdminListFactorsResponseParser: TypeAdapter[AuthMFAAdminListFactorsResponse] = (
    TypeAdapter(AuthMFAAdminListFactorsResponse)
)


class GenerateLinkProperties(BaseModel):
    """
    The properties related to the email link generated.
    """

    action_link: str
    """
    The email link to send to the user. The action_link follows the following format:

    auth/v1/verify?type={verification_type}&token={hashed_token}&redirect_to={redirect_to}
    """
    email_otp: str
    """
    The raw email OTP.
    You should send this in the email if you want your users to verify using an
    OTP instead of the action link.
    """
    hashed_token: str
    """
    The hashed token appended to the action link.
    """
    redirect_to: str
    """
    The URL appended to the action link.
    """
    verification_type: GenerateLinkType
    """
    The verification type that the email link is associated to.
    """


class GenerateLinkResponse(BaseModel):
    properties: GenerateLinkProperties
    user: User


SignOutScope = Literal["global", "local", "others"]


class JWTHeader(BaseModel, extra="allow"):
    alg: Literal["RS256", "ES256", "HS256"]
    typ: str
    kid: str | None = None


class JWTPayload(BaseModel, extra="allow"):
    iss: str | None = None
    sub: str | None = None
    auth: str | list[str] | None = None
    exp: int | None = None
    iat: int | None = None
    role: str | None = None
    aal: AuthenticatorAssuranceLevels | None = None
    session_id: str | None = None
    amr: list[AMREntryDict] | None = None


@dataclass
class ClaimsResponse:
    claims: JWTPayload
    headers: JWTHeader
    signature: bytes


class JWK(BaseModel, extra="allow"):
    kty: Literal["RSA", "EC", "oct"]
    key_ops: list[str]
    alg: str | None = None
    kid: str | None = None


class JWKSet(BaseModel):
    keys: list[JWK]


OAuthClientGrantType = Literal["authorization_code", "refresh_token"]
"""
OAuth client grant types supported by the OAuth 2.1 server.
Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.
"""

OAuthClientResponseType = Literal["code"]
"""
OAuth client response types supported by the OAuth 2.1 server.
Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.
"""

OAuthClientType = Literal["public", "confidential"]
"""
OAuth client type indicating whether the client can keep credentials confidential.
Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.
"""

OAuthClientRegistrationType = Literal["dynamic", "manual"]
"""
OAuth client registration type.
Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.
"""

OAuthClientTokenEndpointAuthMethod = Literal[
    "none", "client_secret_basic", "client_secret_post"
]
"""
OAuth client token endpoint authentication method.
Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.
"""


class OAuthClient(BaseModel):
    """
    OAuth client object returned from the OAuth 2.1 server.
    Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.
    """

    client_id: str
    """Unique client identifier"""
    client_name: str
    """Human-readable name of the client application"""
    client_secret: str | None = None
    """Client secret for confidential clients (only returned on registration/regeneration)"""
    client_type: OAuthClientType
    """Type of the client"""
    token_endpoint_auth_method: OAuthClientTokenEndpointAuthMethod
    """Authentication method for the token endpoint"""
    registration_type: OAuthClientRegistrationType
    """Registration type of the client"""
    client_uri: str | None = None
    """URL of the client application's homepage"""
    logo_uri: str | None = None
    """URL of the client application's logo"""
    redirect_uris: list[str]
    """Array of redirect URIs used by the client"""
    grant_types: list[OAuthClientGrantType]
    """OAuth grant types the client is authorized to use"""
    response_types: list[OAuthClientResponseType]
    """OAuth response types the client can use"""
    scope: str | None = None
    """Space-separated list of scope values"""
    created_at: str
    """Timestamp when the client was created"""
    updated_at: str
    """Timestamp when the client was last updated"""


class CreateOAuthClientParams(BaseModel):
    """
    Parameters for creating a new OAuth client.
    Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.
    """

    client_name: str
    """Human-readable name of the OAuth client"""
    client_uri: str | None = None
    """URL of the client application's homepage"""
    logo_uri: str | None = None
    """URL of the client application's logo"""
    redirect_uris: list[str]
    """Array of redirect URIs used by the client"""
    grant_types: list[OAuthClientGrantType] | None = None
    """OAuth grant types the client is authorized to use (optional, defaults to authorization_code and refresh_token)"""
    response_types: list[OAuthClientResponseType] | None = None
    """OAuth response types the client can use (optional, defaults to code)"""
    scope: str | None = None
    """Space-separated list of scope values"""


class UpdateOAuthClientParams(BaseModel):
    """
    Parameters for updating an existing OAuth client.
    Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.
    """

    client_name: str | None = None
    """Human-readable name of the OAuth client"""
    client_uri: str | None = None
    """URI of the OAuth client"""
    logo_uri: str | None = None
    """URI of the OAuth client's logo"""
    redirect_uris: list[str] | None = None
    """Array of allowed redirect URIs"""
    grant_types: list[OAuthClientGrantType] | None = None
    """Array of allowed grant types"""


class OAuthClientResponse(BaseModel):
    """
    Response type for OAuth client operations.
    Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.
    """

    client: OAuthClient | None = None


class Pagination(BaseModel):
    """
    Pagination information for list responses.
    """

    next_page: int | None = None
    last_page: int = 0
    total: int = 0


class OAuthClientListResponse(BaseModel):
    """
    Response type for listing OAuth clients.
    Only relevant when the OAuth 2.1 server is enabled in Supabase Auth.
    """

    clients: list[OAuthClient]
    aud: str | None = None
    next_page: int | None = None
    last_page: int = 0
    total: int = 0
