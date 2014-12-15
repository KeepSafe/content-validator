from unittest import TestCase
from validator import validator, FileFormat


class TestValidator(TestCase):

    def setUp(self):
        pass

    def test_validate_markdown_structure_happy_path(self):
        res = validator(FileFormat.md) \
            .files('tests/fixtures/{lang}/markdown1.md') \
            .parse() \
            .check_structure() \
            .run()

        self.assertTrue(res)
