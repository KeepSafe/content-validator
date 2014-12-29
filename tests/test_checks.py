from unittest import TestCase
from unittest.mock import patch, MagicMock

from validator.checks import LinkCheck, StructureCheck, MarkdownCheck


class TestLinkCheck(TestCase):
    def setUp(self):
        self.check = LinkCheck()
        self.parser = MagicMock()
        self.reader = MagicMock()

    @patch('requests.get')
    def test_links_happy_path(self, mock_get):
        mock_get.return_value.status_code = 200
        self.parser.parse.return_value = '<a href="www.test.com">test</p>'
        errors = self.check.validate(self.parser, self.reader, 'dummy_path')
        self.assertFalse(errors)


class TestStructureCheck(TestCase):
    def setUp(self):
        self.check = StructureCheck()
        self.parser = MagicMock()
        self.reader = MagicMock()

    def test_structure_happy_path(self):
        self.parser.parse.return_value = '<a>link</a><p>hello</p>'
        errors = self.check.compare(self.parser, self.reader, 'dummy_path', 'dummy_path')
        self.assertFalse(errors)

    def test_structure_different_html(self):
        self.parser.parse.side_effect = ['<a>link</a><p>hello</p>', '<a>link</a><p>hello</p><p>extra</p>']
        errors = self.check.compare(self.parser, self.reader, 'dummy_path', 'dummy_path')
        self.assertTrue(errors)

class TestMarkdownCheck(TestCase):
    def setUp(self):
        self.check = MarkdownCheck()
        self.parser = MagicMock()
        self.reader = MagicMock()

    def test_markdown_happy_path(self):
        self.reader.read.return_value = '[link](http://www.google.com) hello \n\n world'
        errors = self.check.compare(self.parser, self.reader, 'dummy_path', 'dummy_path')
