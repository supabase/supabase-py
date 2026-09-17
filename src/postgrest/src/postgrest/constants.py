from datetime import datetime
from typing import Final, cast

DEFAULT_POSTGREST_CLIENT_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
}

DEFAULT_POSTGREST_CLIENT_TIMEOUT = 120

# PostgreSQL recognizes this string as the current transaction timestamp. The
# cast lets generated update types accept it for datetime columns while keeping
# the value sent to PostgREST unchanged.
NOW: Final[datetime] = cast(datetime, "now()")
