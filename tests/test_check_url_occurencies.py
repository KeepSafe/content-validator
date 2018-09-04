from unittest import TestCase
from unittest.mock import MagicMock

from validator.checks import url


def read(path):
    with open(path) as fp:
        return fp.read()


class TestUrlOccurenciesValidator(TestCase):
    def setUp(self):
        self.parser = MagicMock()
        self.reader = MagicMock()
        self.check = url.UrlOccurenciesValidator('txt')

    def _test_urloccurences(self, path1, path2):
        self.parser.parse.side_effect = lambda val: val
        self.reader.read.side_effect = lambda x: read(x)
        return self.check.check([[path1, path2]], self.parser, self.reader)

    def test_urloccurences_same(self):
        diffs = self._test_urloccurences('tests/fixtures/lang/en/url_occurences_test.txt',
                                         'tests/fixtures/lang/de/url_occurences_test.txt')
        self.assertEqual([], diffs)

    def test_urloccurences_different(self):
        diffs = self._test_urloccurences('tests/fixtures/lang/en/url_occurences_diff.txt',
                                         'tests/fixtures/lang/de/url_occurences_diff.txt')

        self.assertEqual(1, len(diffs))
