class RequestError(Exception):
    """ Rappresents an error in the request with a status_code """

    def __init__(self, status_code, error, message="An error accoured in the request "):
        self.status_code = status_code
        self.error = error
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"A request with status_code {self.status_code} gave an error: {self.error} with this message {self.message}"
