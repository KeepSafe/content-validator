from unittest import TestCase
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import os
import shutil
from . import AsyncTestCase

import validator


class TestUrls(AsyncTestCase):

    def _test_plain_text(self):
        return validator.parse().files('tests/fixtures/flat/test.en.txt').check().url().validate()

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
        validator.parse().files('tests/fixtures/flat/url_with_params.md').md().check().url().validate()
        self.assertFalse(mock_get.called)


class TestMarkdown(TestCase):

    def test_markdown_same_structure(self):
        errors = validator.parse().files('tests/fixtures/lang/{lang}/test1.md', lang='en').check().md().validate()

        self.assertEqual([], errors)

    def test_markdown_different_structure(self):
        errors = validator.parse().files('tests/fixtures/lang/{lang}/test2.md', lang='en').check().md().validate()

        self.assertNotEqual([], errors)

    def test_markdown_single(self):
        errors = validator.parse().file(
            'tests/fixtures/lang/en/test1.md', 'tests/fixtures/lang/en/test1.md').check().md().validate()

        self.assertEqual([], errors)


class TestReporter(TestCase):

    def setUp(self):
        self.output_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.output_dir)

    def test_report_saved(self):
        validator \
            .parse() \
            .files('tests/fixtures/lang/{lang}/test2.md', lang='en') \
            .check() \
            .md() \
            .report() \
            .html(self.output_dir) \
            .validate()

        self.assertNotEqual([], os.listdir(self.output_dir))


class TestBugs(TestCase):

    def _run_and_assert(self, query, **kwargs):
        errors = validator.parse().files(query, **kwargs).md().check().url().validate()

        self.assertEqual([], errors)

    def test_markdown_text_continuation_characters(self):
        self._run_and_assert('tests/fixtures/bugs/continuations.{lang}.md', lang='en')

    def test_markdown_text_code_block(self):
        self._run_and_assert('tests/fixtures/bugs/code_block.{lang}.md', lang='en')

    def test_markdown_text_order(self):
        self._run_and_assert('tests/fixtures/bugs/ignore_order_in_text.{lang}.md', lang='en')


class TestText(TestCase):

    def test_same(self):
        t1 = '##aaa\n\naaa'
        t2 = '##bbb\n\nbbb'
        errors = validator.parse().text(t1, t2).check().md().validate()
        self.assertEqual([], errors)

    def test_different(self):
        t1 = '##aaa\n\naaa'
        t2 = '#bbb\n\nbbb'
        errors = validator.parse().text(t1, t2).check().md().validate()
        self.assertNotEqual([], errors)


class TestJava(TestCase):
    def test_arg_same(self):
        t1 = 'aaa %1.2s aaa'
        t2 = 'bbb %1.2s bbb'
        errors = validator.parse().text(t1, t2).check().java().validate()
        self.assertEqual([], errors)

    def test_arg_different(self):
        t1 = 'aaa %1.2s aaa'
        t2 = 'bbb bbb'
        errors = validator.parse().text(t1, t2).check().java().validate()
        self.assertNotEqual([], errors)

    def test_ref_same(self):
        t1 = '@string/string_name'
        t2 = '@string/string_name'
        errors = validator.parse().text(t1, t2).check().java().validate()
        self.assertEqual([], errors)

    def test_ref_different(self):
        t1 = '@string/string_name'
        t2 = '@string/string_name aaa'
        errors = validator.parse().text(t1, t2).check().java().validate()
        self.assertNotEqual([], errors)
