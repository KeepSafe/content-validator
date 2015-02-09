from unittest import TestCase
from unittest.mock import patch
from pathlib import Path

import validator
import validator.checks
import validator.fs
import validator.parsers
import validator.reports


class TestUrls(TestCase):

    def _test_plain_text(self):
        files = validator.fs.files('tests/fixtures/flat/test.en.txt')
        urls = validator.checks.urls_txt()
        v = validator.Validator(checks=[urls], files=files)
        return v.validate()

    @patch('requests.get')
    def test_plain_text_success(self, mock_get):
        mock_get.return_value.status_code = 200
        errors = self._test_plain_text()
        self.assertEqual({}, errors)

    @patch('requests.get')
    def test_plain_text_failure(self, mock_get):
        mock_get.return_value.status_code = 404
        errors = self._test_plain_text()
        self.assertTrue(Path('tests/fixtures/flat/test.en.txt') in errors)

    @patch('requests.get')
    def test_md_with_params(self, mock_get):
        files = validator.fs.files('tests/fixtures/flat/url_with_params.md')
        urls = validator.checks.urls_html()
        parser = validator.parsers.create_parser(validator.fs.Filetype.md)

        validator.Validator(checks=[urls], files=files, parser=parser).validate()

        self.assertFalse(mock_get.called)


class TestMarkdown(TestCase):

    def test_markdown_same_structure(self):
        files = validator.fs.files('tests/fixtures/lang/{lang}/test1.md', lang='en')
        comparator = validator.checks.markdown()
        v = validator.Validator(checks=[comparator], files=files)

        errors = v.validate()

        self.assertEqual({}, errors)

    def test_markdown_different_structure(self):
        files = validator.fs.files('tests/fixtures/lang/{lang}/test2.md', lang='en')
        comparator = validator.checks.markdown()
        v = validator.Validator(checks=[comparator], files=files)

        errors = v.validate()

        self.assertNotEqual({}, errors)
