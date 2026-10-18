from __future__ import annotations

from datetime import datetime

GOTRUE_URL = "http://localhost:9999"
EXPIRY_MARGIN = 10  # seconds
MAX_RETRIES = 10
RETRY_INTERVAL = 2  # deciseconds
STORAGE_KEY = "supabase.auth.token"

# PKCE code verifiers are stored in one slot per flow so that overlapping flows
# (two OAuth sign-ins, or an OAuth flow started while another is pending) do
# not overwrite each other. The ring is bounded; the oldest pending flow is
# evicted once this many flows are in progress.
PKCE_MAX_CONCURRENT_FLOWS = 5
# Flow ids are concatenated into storage keys, so anything that reaches a key
# (caller-supplied ids and ids read back from storage) must match this shape.
PKCE_FLOW_ID_PATTERN = r"^[a-zA-Z0-9_-]{8,64}$"

API_VERSION_HEADER_NAME = "X-Supabase-Api-Version"
API_VERSIONS_2024_01_01_TIMESTAMP = datetime.timestamp(
    datetime.strptime("2024-01-01", "%Y-%m-%d")
)
API_VERSIONS_2024_01_01_NAME = "2024-01-01"
BASE64URL_REGEX = r"^([a-z0-9_-]{4})*($|[a-z0-9_-]{3}$|[a-z0-9_-]{2}$)$"
