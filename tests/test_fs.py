from unittest import TestCase
from unittest.mock import patch
from pathlib import Path

from validator.fs import files


class TestPaths(TestCase):

    def test_simple(self):
        expected = [[Path('tests/fixtures/flat/test.en.txt')]]

        actual = list(files('tests/fixtures/flat/test.en.txt'))

        self.assertEqual(expected, actual)

    def test_wildcard(self):
        expected = [[Path('tests/fixtures/flat/test.en.txt'), Path('tests/fixtures/flat/test.fr.txt')]]

        actual = list(files('tests/fixtures/flat/*.txt'))

        self.assertEqual(expected, actual)

    def test_recursive(self):
        expected = [[Path('tests/fixtures/lang/de/test1.md'), Path('tests/fixtures/lang/en/test1.md')]]

        actual = list(files('tests/fixtures/lang/**/test1.md'))

        self.assertEqual(expected, actual)


    def test_simple_with_parameter(self):
        expected = [[Path('tests/fixtures/flat/test.en.txt'), Path('tests/fixtures/flat/test.fr.txt')]]

        actual = list(files('tests/fixtures/flat/test.{lang}.txt', lang='en'))

        self.assertEqual(expected, actual)

    def test_wildcard_with_parameter(self):
        expected = [[Path('tests/fixtures/flat/test.en.txt'), Path('tests/fixtures/flat/test.fr.txt')]]

        actual = list(files('tests/fixtures/flat/*.{lang}.txt', lang='en'))

        self.assertEqual(expected, actual)

    def test_wildcard_recursive_with_parameter(self):
        expected = [
            [Path('tests/fixtures/lang/en/test1.md'), Path('tests/fixtures/lang/en/test2.md')],
            [Path('tests/fixtures/lang/de/test1.md'), Path('tests/fixtures/lang/de/test2.md')]
        ]

        actual = list(files('tests/fixtures/lang/**/{order}.md', order='test1'))

        for item in expected:
            self.assertTrue(item in actual)

    def test_two_parameters(self):
        expected = [[Path('tests/fixtures/lang/en/test1.md'), Path('tests/fixtures/lang/de/test1.md')]]

        actual = list(files('tests/fixtures/lang/{lang}/{order}1.md', lang='en', order='test'))

        self.assertEqual(expected, actual)

    def test_fail_on_missing_parameter(self):
        with self.assertRaises(ValueError):
            files('tests/fixtures/flat/test.{lang}.txt')
