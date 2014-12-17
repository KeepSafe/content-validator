from unittest import TestCase
from unittest.mock import patch

from validator.checks import LinkCheck, StructureCheck
from validator.result import ValidationResult


class TestLinkCheck(TestCase):
    def setUp(self):
        self.check = LinkCheck(ValidationResult())

    @patch('requests.get')
    def test_links_happy_path(self, mock_get):
        mock_get.return_value.status_code = 200
        content = '#header'
        self.check.check(content)
        self.assertTrue(self.check.result)


class TestStructureCheck(TestCase):
    def setUp(self):
        self.check = StructureCheck(ValidationResult())

    def test_structure_happy_path(self):
        html = '<a>link</a><p>hello</p>'
        self.check.set_original(html)
        self.check.check(html)
        self.assertTrue(self.check.result)

    def test_structure_different_html(self):
        html = '<a>link</a><p>hello</p>'
        self.check.set_original(html)
        self.check.check(html + '<p>extra</p>')
        self.assertFalse(self.check.result)
