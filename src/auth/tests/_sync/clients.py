from jwt import encode

from supabase_auth import SyncGoTrueAdminAPI, SyncGoTrueClient

SIGNUP_ENABLED_AUTO_CONFIRM_OFF_PORT = 9999
SIGNUP_ENABLED_AUTO_CONFIRM_ON_PORT = 9998
SIGNUP_DISABLED_AUTO_CONFIRM_OFF_PORT = 9997
SIGNUP_ENABLED_ASYMMETRIC_AUTO_CONFIRM_ON_PORT = 9996

GOTRUE_URL_SIGNUP_ENABLED_AUTO_CONFIRM_OFF = (
    f"http://localhost:{SIGNUP_ENABLED_AUTO_CONFIRM_OFF_PORT}"
)
GOTRUE_URL_SIGNUP_ENABLED_AUTO_CONFIRM_ON = (
    f"http://localhost:{SIGNUP_ENABLED_AUTO_CONFIRM_ON_PORT}"
)
GOTRUE_URL_SIGNUP_ENABLED_ASYMMETRIC_AUTO_CONFIRM_ON = (
    f"http://localhost:{SIGNUP_ENABLED_ASYMMETRIC_AUTO_CONFIRM_ON_PORT}"
)
GOTRUE_URL_SIGNUP_DISABLED_AUTO_CONFIRM_OFF = (
    f"http://localhost:{SIGNUP_DISABLED_AUTO_CONFIRM_OFF_PORT}"
)

GOTRUE_JWT_SECRET = "37c304f8-51aa-419a-a1af-06154e63707a"

AUTH_ADMIN_JWT = encode(
    {
        "sub": "1234567890",
        "role": "supabase_admin",
    },
    GOTRUE_JWT_SECRET,
)


def auth_client():
    return SyncGoTrueClient(
        url=GOTRUE_URL_SIGNUP_ENABLED_AUTO_CONFIRM_ON,
        auto_refresh_token=False,
        persist_session=True,
    )


def auth_client_with_session():
    return SyncGoTrueClient(
        url=GOTRUE_URL_SIGNUP_ENABLED_AUTO_CONFIRM_ON,
        auto_refresh_token=False,
        persist_session=False,
    )


def auth_client_with_asymmetric_session() -> SyncGoTrueClient:
    return SyncGoTrueClient(
        url=GOTRUE_URL_SIGNUP_ENABLED_ASYMMETRIC_AUTO_CONFIRM_ON,
        auto_refresh_token=False,
        persist_session=False,
    )


def auth_subscription_client():
    return SyncGoTrueClient(
        url=GOTRUE_URL_SIGNUP_ENABLED_AUTO_CONFIRM_ON,
        auto_refresh_token=False,
        persist_session=True,
    )


def client_api_auto_confirm_enabled_client():
    return SyncGoTrueClient(
        url=GOTRUE_URL_SIGNUP_ENABLED_AUTO_CONFIRM_ON,
        auto_refresh_token=False,
        persist_session=True,
    )


def client_api_auto_confirm_off_signups_enabled_client():
    return SyncGoTrueClient(
        url=GOTRUE_URL_SIGNUP_ENABLED_AUTO_CONFIRM_OFF,
        auto_refresh_token=False,
        persist_session=True,
    )


def client_api_auto_confirm_disabled_client():
    return SyncGoTrueClient(
        url=GOTRUE_URL_SIGNUP_DISABLED_AUTO_CONFIRM_OFF,
        auto_refresh_token=False,
        persist_session=True,
    )


def auth_admin_api_auto_confirm_enabled_client():
    return SyncGoTrueAdminAPI(
        url=GOTRUE_URL_SIGNUP_ENABLED_AUTO_CONFIRM_ON,
        headers={
            "Authorization": f"Bearer {AUTH_ADMIN_JWT}",
        },
    )


def auth_admin_api_auto_confirm_disabled_client():
    return SyncGoTrueAdminAPI(
        url=GOTRUE_URL_SIGNUP_ENABLED_AUTO_CONFIRM_OFF,
        headers={
            "Authorization": f"Bearer {AUTH_ADMIN_JWT}",
        },
    )


SERVICE_ROLE_JWT = encode(
    {
        "role": "service_role",
    },
    GOTRUE_JWT_SECRET,
)


def service_role_api_client():
    return SyncGoTrueAdminAPI(
        url=GOTRUE_URL_SIGNUP_ENABLED_AUTO_CONFIRM_ON,
        headers={
            "Authorization": f"Bearer {SERVICE_ROLE_JWT}",
        },
    )


def service_role_api_client_with_sms():
    return SyncGoTrueAdminAPI(
        url=GOTRUE_URL_SIGNUP_ENABLED_AUTO_CONFIRM_OFF,
        headers={
            "Authorization": f"Bearer {SERVICE_ROLE_JWT}",
        },
    )


def service_role_api_client_no_sms():
    return SyncGoTrueAdminAPI(
        url=GOTRUE_URL_SIGNUP_DISABLED_AUTO_CONFIRM_OFF,
        headers={
            "Authorization": f"Bearer {SERVICE_ROLE_JWT}",
        },
    )
