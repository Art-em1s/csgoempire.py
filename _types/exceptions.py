class CustomError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class ApiKeyMissing(CustomError):
    def __init__(self):
        super().__init__("No token provided, please generate a token at https://csgoempire.com/trading/apikey")


class InvalidApiKey(CustomError):
    def __init__(self):
        super().__init__("Invalid token provided, please generate a token at https://csgoempire.com/trading/apikey")


class RequestError(CustomError):
    pass


class InvalidDomain(CustomError):
    pass


class ExceedsRatelimit(CustomError):
    pass


def handle_error(status, response, class_name, function_name):
    exception_mapping = {
        401: InvalidApiKey,
        429: ExceedsRatelimit
    }
    exception_class = exception_mapping.get(status, RequestError)
    raise exception_class(f"{class_name}:{function_name}:{status}: {response['message']}")
