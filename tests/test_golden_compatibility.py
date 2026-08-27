import hashlib
import json
from importlib.metadata import version
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

import validator
from bs4 import BeautifulSoup
from validator.checks.url import TextUrlExtractor


FIXTURES = Path('tests/fixtures')
ZENDESK_GOLDEN = FIXTURES / 'golden' / 'zendesk_sdiff_2_0.json'
ZENDESK_REPORT_GOLDEN = FIXTURES / 'golden' / 'zendesk_sdiff_2_0_report.json'


def _zendesk_validation(name):
    pattern = str(FIXTURES / 'zendesk' / f'{name}.{{lang}}.md')
    return validator.parse().files(pattern, lang='en').check().zendesk_helpcenter_md().validate()


def _content_snapshot(content):
    return {
        'original': str(content.original),
        'parsed': content.parsed,
        'diff': content.diff,
        'html': content.html,
    }


class TestGoldenCompatibility(TestCase):
    maxDiff = None

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

    def test_zendesk_nested_components_same_structure(self):
        self.assertEqual([], _zendesk_validation('equivalent'))

    def test_zendesk_nested_components_diff_shape(self):
        errors = _zendesk_validation('different')

        self.assertEqual(1, len(errors))
        error = errors[0]
        actual = {
            'error_messages': list(error.error_msgs),
            'base': _content_snapshot(error.base),
            'other': _content_snapshot(error.other),
        }
        expected = json.loads(ZENDESK_GOLDEN.read_text(encoding='utf-8'))
        self.assertEqual(expected, actual)

    def test_zendesk_html_report_matches_golden(self):
        pattern = str(FIXTURES / 'zendesk' / 'different.{lang}.md')
        with TemporaryDirectory() as output_directory:
            errors = validator.parse().files(pattern, lang='en') \
                .check().zendesk_helpcenter_md().report().html(output_directory).validate()
            report_path = Path(output_directory) / errors[0].other.original.with_suffix('.html')
            report = report_path.read_text(encoding='utf-8')

        soup = BeautifulSoup(report, 'html.parser')
        actual = {
            'sha256': hashlib.sha256(report.encode('utf-8')).hexdigest(),
            'left_content_text': list(soup.select_one('#left_content').stripped_strings),
            'right_content_text': list(soup.select_one('#right_content').stripped_strings),
            'left_diff_text': soup.select_one('#left_diff').get_text('\n', strip=True),
            'right_diff_text': soup.select_one('#right_diff').get_text('\n', strip=True),
            'error_messages': list(soup.select_one('#error_msgs').stripped_strings),
        }
        expected = json.loads(ZENDESK_REPORT_GOLDEN.read_text(encoding='utf-8'))
        self.assertEqual(expected, actual)

    def test_installed_sdiff_dependency_versions(self):
        self.assertEqual('1.0.0', version('content-validator'))
        self.assertEqual('2.0.0', version('sdiff'))
        self.assertEqual('3.3.4', version('mistune'))
        self.assertEqual('6.0.2', version('lxml'))
