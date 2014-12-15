from .checks import Checker

class MarkdownParser(object):
    def __init__(self, files):
        self.files = files

    def _content(self, files):
        return {}

    def parse(self):
        content = self._content(self.files)
        return Checker()
