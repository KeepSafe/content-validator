from unittest import TestCase
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import os
import shutil
from . import AsyncTestCase

import validator
import validator.checks
import validator.fs
import validator.parsers
import validator.reports


class TestUrls(AsyncTestCase):

    def _test_plain_text(self):
        files = validator.fs.files('tests/fixtures/flat/test.en.txt')
        urls = validator.checks.urls(validator.fs.Filetype.txt)
        return validator.validate(checks=[urls], files=files)

    @patch('aiohttp.request')
    def test_plain_text_success(self, mock_get):
        res = MagicMock()
        res.status = 200
        mock_get.return_value = self.make_fut(res)
        errors = self._test_plain_text()
        self.assertEqual([], errors)

    @patch('aiohttp.request')
    def test_plain_text_failure(self, mock_get):
        res = MagicMock()
        res.status = 404
        mock_get.return_value = self.make_fut(res)
        errors = self._test_plain_text()
        self.assertTrue(Path('tests/fixtures/flat/test.en.txt') in errors[0].files)

    @patch('aiohttp.request')
    def test_md_with_params(self, mock_get):
        files = validator.fs.files('tests/fixtures/flat/url_with_params.md')
        urls = validator.checks.urls(validator.fs.Filetype.html)
        parser = validator.parsers.create_parser(validator.fs.Filetype.md)

        validator.validate(checks=[urls], files=files, parser=parser)

        self.assertFalse(mock_get.called)


class TestMarkdown(TestCase):

    def setUp(self):
        self.comparator = validator.checks.markdown()

    def test_markdown_same_structure(self):
        files = validator.fs.files('tests/fixtures/lang/{lang}/test1.md', lang='en')

        errors = validator.validate(checks=[self.comparator], files=files)

        self.assertEqual([], errors)

    def test_markdown_different_structure(self):
        files = validator.fs.files('tests/fixtures/lang/{lang}/test2.md', lang='en')

        errors = validator.validate(checks=[self.comparator], files=files)

        self.assertNotEqual([], errors)

class TestReporter(TestCase):

    def setUp(self):
        self.output_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.output_dir)

    def test_report_saved(self):
        files = validator.fs.files('tests/fixtures/lang/{lang}/test2.md', lang='en')
        comparator = validator.checks.markdown()
        reporter = validator.reports.HtmlReporter(output_directory=self.output_dir)

        validator.validate(checks=[comparator], files=files, reporter=reporter)

        self.assertNotEqual([], os.listdir(self.output_dir))

class TestBugs(TestCase):

    def setUp(self):
        self.comparator = validator.checks.markdown()

    def test_markdown_text_continuation_characters(self):
        files = validator.fs.files('tests/fixtures/bugs/continuations.{lang}.md', lang='en')

        errors = validator.validate(checks=[self.comparator], files=files)

        self.assertEqual([], errors)

    def test_markdown_text_code_block(self):
        files = validator.fs.files('tests/fixtures/bugs/code_block.{lang}.md', lang='en')

        errors = validator.validate(checks=[self.comparator], files=files)

        self.assertEqual([], errors)
