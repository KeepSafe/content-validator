import os

from .files import files
from .parser import parser
from .checks import check, CheckType
from .utils import FileFormat
from .result import ValidationResult


class Validator(object):

    def __init__(self, file_format):
        self._file_format = file_format
        self._checks = []
        self.result = ValidationResult()

    def files(self, pattern='*', directory=None, lang='en-US'):
        self.directory = directory or os.getcwd()
        self._files = files(pattern, self.directory, lang)
        return self

    def parse(self, file_format=None, **kwargs):
        file_format = file_format or self._file_format
        self._parser = parser(file_format, **kwargs)
        return self

    def check_structure(self):
        self._checks.append(check(CheckType.structure, self.result))
        return self

    def check_links(self):
        self._checks.append(check(CheckType.link, self.result))
        return self

    def run(self):
        for lang_files in self._files:
            original_file = lang_files.pop()
            original_path = os.path.join(self.directory, original_file)
            original_content = self._parser.parse(original_path)
            for checker in self._checks:
                checker.set_original(original_content)
                for lang_file in lang_files:
                    print('compering {} with {}'.format(original_file, lang_file))
                    lang_path = os.path.join(self.directory, lang_file)
                    content = self._parser.parse(lang_path)
                    checker.check(content)
        return self.result


def validator(file_format):
    return Validator(file_format)
