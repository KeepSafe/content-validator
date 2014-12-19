from unittest import TestCase
from unittest.mock import MagicMock, patch

from validator.diff import Diff

class TestDiff(TestCase):
    def setUp(self):
        self.diff = Diff('/path/to/dir')
        self.parser = MagicMock()

    @patch('os.makedirs')
    def test_diff_happy_path(self, mock_open):
        m = mock_open()
        with patch('builtins.open', m, create=True):
            self.parser.parse.side_effect = ['<body><p>hello</p></body>', '<body><p>hello</p><p>world</p></body>']
            self.diff.diff_to_file(self.parser, '/path/to/dummy1.py', '/path/to/dummy1.py')
        self.assertTrue(m().__enter__().write.called)

    def test_get_lang(self):
        lang = self.diff._get_lang('/path/to/en/file.md', '/path/to/fr/file.md')
        self.assertEqual('fr', lang)
