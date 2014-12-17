import os
from unittest import TestCase

from validator.files import files
from validator.utils import FileFormat


class TestFiles(TestCase):
    def setUp(self):
        pass

    def test_resolve_all_files(self):
        actual = files('tests/fixtures/{lang}/markdown*.md', lang='en')
        self.assertEqual([['tests/fixtures/fr/markdown1.md', 'tests/fixtures/en/markdown1.md']], list(actual))

    def test_use_custom_directory(self):
        actual = files('{lang}/markdown*.md', directory='tests/fixtures', lang='en')
        self.assertEqual([['fr/markdown1.md', 'en/markdown1.md']], list(actual))
