class ValidationError(object):
    def __init__(self, reason):
        self.reason = reason

class ValidationResult(object):
    def __init__(self):
        self.errors = []

    def __bool__(self):
        return len(self.errors) == 0
