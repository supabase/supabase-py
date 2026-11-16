from supabase_utils.errors import SupabaseError

__all__ = ["SupabaseException"]


class SupabaseException(SupabaseError):
    """Raised when the client is created with a missing or invalid URL or key, or
    when `auth` is used on a client returned by `with_token()`."""
