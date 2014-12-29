from unittest import TestCase
from unittest.mock import patch
from validator import validator, FileFormat


class TestValidator(TestCase):

    def setUp(self):
        pass

    @patch('requests.get')
    def test_validate_markdown_link_happy_path(self, mock_get):
        mock_get.return_value.status_code = 200
        res = validator(FileFormat.md) \
            .files('tests/fixtures/{lang}/*.md', lang='en') \
            .read(FileFormat.txt) \
            .check_links() \
            .run()

        self.assertFalse(res)

    @patch('requests.get')
    def test_validate_markdown_link_fail(self, mock_get):
        mock_get.return_value.status_code = 500
        res = validator(FileFormat.md) \
            .files('tests/fixtures/{lang}/*.md', lang='en') \
            .read(FileFormat.txt) \
            .check_links() \
            .run()

        self.assertTrue(res)

    def test_validate_markdown_structure_happy_path(self):
        res = validator(FileFormat.md) \
            .files('tests/fixtures/{lang}/*.md', lang='en') \
            .read(FileFormat.txt) \
            .check_structure() \
            .run()

        self.assertFalse(res)

    def test_validate_xml_structure_happy_path(self):
        res = validator(FileFormat.md) \
            .files('tests/fixtures/{lang}/markdown_in_xml.xml', lang='en') \
            .read(FileFormat.xml, query='.//string') \
            .check_markdown() \
            .run()

        self.assertFalse(res)

    def test_validate_xml_structure_extra_path(self):
        res = validator(FileFormat.md) \
            .files('tests/fixtures/{lang}/markdown_in_xml_extra_tag.xml', lang='en') \
            .read(FileFormat.xml, query='.//string') \
            .check_markdown() \
            .run()
        
        self.assertTrue(res)
