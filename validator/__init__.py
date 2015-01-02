import os

from .files import files
from .parser import parser, reader
from .checks import check_links, check_structure, check_markdown, RecordPattern, ReplayPattern
from .diff import diff
from .utils import FileFormat
from .errors import ValidationError


class Validator(object):

    def __init__(self, data_format):
        self.data_format = data_format
        self.parser = parser(data_format)
        self.content_checks = []
        self.compare_checks = []
        self.diff = None

    def files(self, pattern='*', directory=None, lang='en-US'):
        self.directory = directory or os.getcwd()
        self.files = files(pattern, self.directory, lang)
        return self

    def read(self, input_format=None, **kwargs):
        input_format = input_format or self.data_format
        self.reader = reader(input_format, **kwargs)
        return self

    def check_structure(self):
        self.compare_checks.append(check_structure())
        return self

    def check_markdown(self):
        self.compare_checks.append(check_markdown())
        return self

    def check_links(self):
        self.content_checks.append(check_links())
        return self

    def save_diff(self, output_directory='output'):
        self.diff = diff(output_directory)
        return self

    def _save_diff(self, errors):
        for error in errors.compare_errors:
            self.diff.html_to_file(self.parser, self.reader, error.base_file_path, error.other_file_path)
            self.diff.diff_to_file(self.parser, self.reader, error.base_file_path, error.other_file_path)
            self.diff.error_to_file(error.base_file_path, error.other_file_path, error)

    def run(self):
        errors = ValidationError()
        for lang_files in self.files:
            for checker in self.content_checks:
                for lang_file in lang_files:
                    file_path = os.path.join(self.directory, lang_file)
                    error = checker.validate(self.parser, self.reader, file_path)
                    if error:
                        errors.add_content_error(error)
            for checker in self.compare_checks:
                base_file = lang_files[-1]
                base_path = os.path.join(self.directory, base_file)
                for lang_file in lang_files[:-1]:
                    file_path = os.path.join(self.directory, lang_file)
                    error = checker.compare(self.parser, self.reader, base_path, file_path)
                    if error:
                        errors.add_compare_error(error)

        if self.diff:
            self._save_diff(errors)

        return errors


def validator(file_format):
    return Validator(file_format)
