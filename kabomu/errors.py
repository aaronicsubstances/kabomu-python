class KabomuError(Exception):
    def __init__(self, *args: object):
        super().__init__(*args)

class KabomuIOError(KabomuError):
    def __init__(self, *args: object):
        super().__init__(*args)

    @staticmethod
    def create_end_of_read_error():
        return KabomuIOError("unexpected end of read")
    
class ExpectationViolationError(KabomuError):
    def __init__(self, *args: object):
        super().__init__(*args)

class MissingDependencyError(KabomuError):
    def __init__(self, *args: object):
        super().__init__(*args)

class IllegalArgumentError(KabomuError):
    def __init__(self, *args: object):
        super().__init__(*args)

QUASI_HTTP_ERROR_REASON_GENERAL = 1
QUASI_HTTP_ERROR_REASON_TIMEOUT = 2
QUASI_HTTP_ERROR_REASON_PROTOCOL_VIOLATION = 3
QUASI_HTTP_ERROR_REASON_MESSAGE_LENGTH_LIMIT_EXCEEDED = 4

class QuasiHttpError(KabomuError):
    def __init__(self, reason_code, *args: object):
        super().__init__(*args)
        if not reason_code or (reason_code > 4 and reason_code < 10):
            raise IllegalArgumentError(f"cannot use reserved reason code: {reason_code}")
        self.reason_code = reason_code 