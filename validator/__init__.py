from enum import Enum
from collections import defaultdict
from pathlib import Path
from markdown import markdown

from sdiff import renderer, diff
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


def validate_single(checks, base_path, other_path, parser=TxtParser(), reporter=None):
    base = Path(base_path)
    other = Path(other_path)
    files = [[base, other]]
    return validate(checks, files, parser, reporter)


def validate_text(checks, base, other, parser=TxtParser(), reporter=None):
    other_diff, base_diff, error = diff(other, base, renderer=renderer.HtmlRenderer())
    if error:
        return HtmlDiff(base_path, markdown(base), base_diff, other_path, markdown(other), other_diff, error)
