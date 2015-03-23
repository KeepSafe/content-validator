from unittest import TestCase
from unittest.mock import patch, MagicMock

from validator.checks import markdown


def read(path):
    with open(path) as fp:
        return fp.read()


class TestMarkdownComparator(TestCase):
    def setUp(self):
        self.parser = MagicMock()
        self.check = markdown()
    
    def _test_markdown(self, mock_read, path1, path2):
        self.parser.parse.side_effect = iter([read(path1), read(path2)])
        return self.check.check([['dummy_path1', 'dummy_path2']], self.parser)

    @patch('validator.checks.html_struct_diff.read_content')
    def test_markdown_same(self, mock_read):
        diffs = self._test_markdown(mock_read, 'tests/fixtures/lang/en/test1.md', 'tests/fixtures/lang/de/test1.md')
        self.assertEqual([], diffs)

    @patch('validator.checks.html_struct_diff.read_content')
    def test_markdown_different(self, mock_read):
        diffs = self._test_markdown(mock_read, 'tests/fixtures/lang/en/test2.md', 'tests/fixtures/lang/de/test2.md')
        
        self.assertEqual(1, len(diffs))
        diff = diffs[0]
        self.assertEqual('dummy_path1', diff.base_path)
        self.assertEqual('dummy_path2', diff.other_path)
        self.assertNotEqual('', diff.diff)
