from unittest import TestCase

import validator
from validator.checks.url import TextUrlExtractor


class TestGoldenCompatibility(TestCase):
    def test_markdown_fixture_diff_shape(self):
        errors = validator.parse().files('tests/fixtures/lang/{lang}/test2.md', lang='en').check().md().validate()

        self.assertEqual(1, len(errors))
        error = errors[0]
        self.assertEqual('tests/fixtures/lang/en/test2.md', str(error.base.original))
        self.assertEqual('tests/fixtures/lang/de/test2.md', str(error.other.original))
        self.assertEqual([
            'There is a missing element `text`.',
            'There is a missing element `header`.',
            'There is a missing element `text`.',
            'There is a missing element `paragraph`.',
            'There is a missing element `text`.',
            'There is a missing element `new-line`.',
            'There is an additional element `header`.',
            'There is an additional element `text`.',
            'There is an additional element `paragraph`.',
            'There is an additional element `text`.',
        ], list(error.error_msgs))

    def test_java_placeholder_fixture_shape(self):
        same_errors = validator.parse().text('aaa %1.2s aaa', 'bbb %1.2s bbb').check().java().validate()
        diff_errors = validator.parse().text('aaa %1.2s aaa', 'bbb bbb').check().java().validate()

        self.assertEqual([], same_errors)
        self.assertEqual(1, len(diff_errors))
        self.assertEqual('java args do not match', diff_errors[0].error_msgs)

    def test_url_extractor_fixture_shape(self):
        urls = TextUrlExtractor().extract_urls(
            'one http://example.com/a?b=1 two http://{{placeholder}} three http://www.google¡.com'
        )

        self.assertEqual(['http://example.com/a?b=1', 'http://www.google.com'], sorted(urls))
