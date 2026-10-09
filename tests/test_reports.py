from validator.errors import ContentData, MdDiff, UrlDiff
from validator.reports import HtmlReporter


def test_html_reporter_handles_url_diff(tmp_path):
    reporter = HtmlReporter(output_directory=str(tmp_path))
    error = UrlDiff('http://example.com', files=['errors/source.md'], status_code=404)

    reporter.report([error])

    report_path = tmp_path / 'errors' / 'source.html'
    assert report_path.exists()
    assert 'http://example.com returned with code 404' in report_path.read_text()


def test_html_reporter_writes_markdown_diff(tmp_path):
    reporter = HtmlReporter(output_directory=str(tmp_path))
    base = ContentData('base.md', 'Base', '<del>Base</del>', '<p>Base</p>')
    other = ContentData('other.md', 'Other', '<ins>Other</ins>', '<p>Other</p>')
    error = MdDiff(base, other, ['Missing content'])

    reporter.report([error])

    report_path = tmp_path / 'other.html'
    assert report_path.exists()
    content = report_path.read_text()
    assert 'Missing content' in content
    assert '<del>' in content
    assert '<ins>' in content
    assert 'Base' in content
    assert 'Other' in content
