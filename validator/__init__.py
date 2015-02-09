from enum import Enum
from collections import defaultdict

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
        file_errors = defaultdict(list)
        for paths in self.files:
            for check in self.checks:
                errors = check.check(paths, self.parser)
                for path, error in errors.items():
                    file_errors[path].append(error)

        if self.reporter:
            self.reporter.report(file_errors)

        return file_errors
