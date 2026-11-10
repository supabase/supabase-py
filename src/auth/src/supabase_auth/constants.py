from __future__ import annotations

GOTRUE_URL = "http://localhost:9999"
EXPIRY_MARGIN = 10  # seconds
MAX_RETRIES = 10
RETRY_BASE_DELAY = 0.2  # seconds
RETRY_MAX_DELAY = 30  # seconds
STORAGE_KEY = "supabase.auth.token"

BASE64URL_REGEX = r"^([a-z0-9_-]{4})*($|[a-z0-9_-]{3}$|[a-z0-9_-]{2}$)$"
