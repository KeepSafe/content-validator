from enum import Enum
from collections import defaultdict

from .parsers import TxtParser
from .reports import ConsoleReporter


def validate(checks=[], files=[], parser=TxtParser(), reporter=None):
    errors = []
    for check in checks:
        check_errors = check.check(files, parser)
        errors.extend(check_errors)
        if reporter is not None:
            reporter.report(check_errors)

    return errors
