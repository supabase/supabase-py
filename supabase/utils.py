# Create an exception class when user does not provide a valid url or key.
class SupabaseException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class AuthProxy:
    def __getattr__(self, attr):
        raise SupabaseException(
            f"Supabase Client is configured with the access_token option, accessing supabase.auth.{attr} is not possible.",
        )
