import os

from .files import files
from .parser import parser
from .checks import check_links, check_structure
from .utils import FileFormat


class Validator(object):

    def __init__(self, file_format):
        self.file_format = file_format
        self.content_checks = []
        self.compare_checks = []

    def files(self, pattern='*', directory=None, lang='en-US'):
        self.directory = directory or os.getcwd()
        self.files = files(pattern, self.directory, lang)
        return self

    def parse(self, file_format=None, **kwargs):
        file_format = file_format or self.file_format
        self.parser = parser(file_format, **kwargs)
        return self

    def check_structure(self):
        self.compare_checks.append(check_structure())
        return self

    def check_links(self):
        self.content_checks.append(check_links())
        return self

    def run(self):
        errors = []
        for lang_files in self.files:
            for checker in self.content_checks:
                for lang_file in lang_files:
                    file_path = os.path.join(self.directory, lang_file)
                    error = checker.validate(self.parser, file_path)
                    if error:
                        errors.append(error)
            for checker in self.compare_checks:
                base_file = lang_files[0]
                base_path = os.path.join(self.directory, base_file)
                for lang_file in lang_files[1:]:
                    file_path = os.path.join(self.directory, lang_file)
                    error = checker.compare(self.parser, base_path, file_path)
                    if error:
                        errors.append(error)
        return errors


def validator(file_format):
    return Validator(file_format)
