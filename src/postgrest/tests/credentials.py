from base64 import b64encode

USERNAME = "test-user"
PASSWORD = "test-password"
TOKEN = "test-token"


def basic_authorization(username: str, password: str) -> str:
    credentials = b64encode(f"{username}:{password}".encode()).decode()
    return f"Basic {credentials}"


BASIC_AUTHORIZATION = basic_authorization(USERNAME, PASSWORD)
BEARER_AUTHORIZATION = f"Bearer {TOKEN}"
