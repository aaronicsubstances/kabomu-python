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
