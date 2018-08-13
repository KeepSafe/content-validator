from .md import MarkdownComparator
from .url import UrlValidator, UrlOccurenciesValidator
from .java import JavaComparator


class UndefinedCheckTypeError(Exception):
    pass


def urls(filetype, **kwargs):
    return UrlValidator(filetype, **kwargs)

def url_occurences(filetype):
    if filetype != 'txt':
        raise UndefinedCheckTypeError('got filetype %s, expected txt' % filetype)
    return UrlOccurenciesValitator()

def markdown(filetype):
    if filetype not in ['txt', 'html']:
        raise UndefinedCheckTypeError('got filetype %s' % filetype)
    return MarkdownComparator()


def java_args(filetype):
    if filetype != 'txt':
        raise UndefinedCheckTypeError('got filetype %s' % filetype)
    return JavaComparator()


class ChainCheck(object):
    def __init__(self, checks):
        self.checks = checks

    def check(self, contents, parser, reader):
        errors = []
        for check in self.checks:
            check_errors = check.check(contents, parser, reader)
            errors.extend(check_errors)
        return errors

    def async_check(self, contents, parser, reader):
        errors = []
        for check in self.checks:
            check_errors = yield from check.async_check(contents, parser, reader)
            errors.extend(check_errors)
        return errors
