from __future__ import annotations

from typing import Any


def _rebuild(
    cls: type[SupabaseError], args: tuple[Any, ...], state: dict[str, Any]
) -> SupabaseError:
    error = cls.__new__(cls)
    error.args = args
    error.__dict__.update(state)
    return error


class SupabaseError(Exception):
    """Base class of every exception the supabase packages raise.

    A plain `SupabaseError` is a failure a client raised on its own, without
    or before a request, such as a missing session or an invalid URL. A
    failure a service answered with is a `SupabaseAPIError`, and a request
    that failed before a response could be read is a `SupabaseTransportError`,
    both in
    `supabase_utils.http.errors`.

    The roots of the packages all inherit from it: `AuthError`,
    `postgrest.APIError`, `StorageException`, `FunctionsError`,
    `RealtimeError` and `SupabaseException`.

    ```python
    try:
        client.table("countries").select("*").execute()
    except SupabaseError as error:
        print(error.message)
    ```
    """

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        """Human readable description of the failure, also returned by `str()`."""
        self.code = code
        """Identifier of the failure, such as `weak_password` (auth), `PGRST116`
        (postgrest) or `NoSuchKey` (storage). None when neither the service nor
        the client named it."""

    def __reduce__(self) -> tuple[Any, ...]:
        # The constructors of the subclasses take different arguments than the
        # ones stored in `args`, so rebuild from the instance state instead.
        return (_rebuild, (type(self), self.args, self.__dict__))
