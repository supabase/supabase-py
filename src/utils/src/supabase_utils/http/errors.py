from .request import Request


class RequestTimeoutError(TimeoutError):
    """Raised when a request to a Supabase service times out."""

    def __init__(self, request: Request) -> None:
        self.request = request
        super().__init__(f"{request.method} {request.url.with_query(None)} timed out")
