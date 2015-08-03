from .md_struct_diff import MarkdownComparator
from .url_validator import UrlValidator


def urls(filetype, **kwargs):
    return UrlValidator(filetype, **kwargs)


def markdown():
    return MarkdownComparator()
