from .md import MarkdownComparator
from .url import UrlValidator


class UndefinedCheckTypeError(Exception):
    pass


def urls(filetype, **kwargs):
    return UrlValidator(filetype, **kwargs)


def markdown(filetype):
    if filetype != 'txt':
        raise UndefinedCheckTypeError('got filetype %s' % filetype)
    return MarkdownComparator()


class ChainCheck(object):
    def __init__(self, checks):
        self.checks = checks

    def check(self, contents, parser):
        errors = []
        for check in self.checks:
            check_errors = check.check(contents, parser)
            errors.extend(check_errors)
        return errors
