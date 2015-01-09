from unittest import TestCase
from unittest.mock import MagicMock, patch

from validator.diff import Diff

class TestDiff(TestCase):
    def setUp(self):
        self.diff = Diff('/path/to/dir')
        self.parser = MagicMock()
        self.reader = MagicMock()

    @patch('os.makedirs')
    def _test_diff_happy_path(self, mock_open):
        m = mock_open()
        with patch('builtins.open', m, create=True):
            self.parser.parse.side_effect = ['<body><p>hello</p></body>', '<body><p>hello</p><p>world</p></body>']
            self.diff.html_to_file(self.parser, self.reader, '/path/to/dummy1.py', '/path/to/dummy1.py')
        self.assertTrue(m().__enter__().write.called)

    def test_get_lang(self):
        lang = self.diff._get_lang('/path/to/en/file.md', '/path/to/fr/file.md')
        self.assertEqual('fr', lang)

    def test_get_lang_same_start(self):
        lang = self.diff._get_lang('/path/to/en/file.md', '/path/to/es/file.md')
        self.assertEqual('es', lang)
