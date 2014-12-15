import os
from .parser import MarkdownParser
from .utils import FileFormat

parsers = {
    FileFormat.md: MarkdownParser
}


class Files(object):

    def __init__(self, file_format):
        self.file_format = file_format

    def _resolve_files(self, pattern='*', directory=None, recursive=True, **kwargs):
        return []

    def files(self, pattern='*', directory=None, recursive=True, **kwargs):
        files = self._resolve_files(pattern='*', directory=None, recursive=True, **kwargs)
        return parsers[self.file_format](files)
