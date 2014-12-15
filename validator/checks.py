from .result import ValidationResult

class LinkCheck(object):
    pass


class StructureCheck(object):
    pass


class Checker(object):

    def check_structure(self):
        return self

    def run(self):
        return ValidationResult()
