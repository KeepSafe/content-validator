from enum import Enum
from .parsers import TxtParser
from .diff import TxtDiffer
from .reports import HtmlReporter

class Validator(object):
    def __init__(self, checks=[], files=[], parser=TxtParser(), reporter=None):
        self.checks = checks
        self.files = files
        self.parser = parser
        self.reporter = reporter

    def validate(self):
        file_errors = {}
        for paths in self.files:
            for check in self.checks:
                errors = check.check(paths, self.parser)
                for path, error in errors.items():
                    if path in file_errors:
                        file_errors[path].extend(error)
                    else:
                        file_errors[path] = error

        if self.reporter:
            self.reporter.report(file_errors)

        return file_errors
