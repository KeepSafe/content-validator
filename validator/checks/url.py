import re
import logging
import asyncio
import aiohttp
import string
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from typing import List, Optional

from ..errors import UrlDiff, UrlOccurencyDiff

logging.getLogger('aiohttp').setLevel(logging.ERROR)
logging.getLogger('asyncio').setLevel(logging.ERROR)

DEFAULT_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/537.36 (KHTML, like Gecko)'\
                     'Chrome/54.0.2806.0 Safari/537.36'


class MissingUrlExtractorError(Exception):
    pass


# the job of extractors is to find all non-parametrized urls in the given text for later checks via UrlValidator
# which examines is particular url leads to working webpage (200 status)
# since we are interested in all urls (including parametrized) we need to sligthly change their API and behaviour
class TextUrlExtractor:
    def __init__(self, **kwargs):
        pass

    url_pattern = r'(?i)\b((?:https?://|www\d{0,3}[.]|(!keepsafe://)[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()\[\]<>]' \
        r'+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[' \
        r'\];:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019]))'

    def _without_params(self, url):
        return not bool(re.search(r'\{[a-zA-Z0-9_.]+\}', url))

    def _strip_non_ascii_chars(self, url):
        return ''.join(filter(lambda c: c in string.printable, url))

    def extract_urls(self, content, unique=True, strip_placeholders=True):
        result = [match.group().strip(').') for match in re.finditer(self.url_pattern, content)]
        if unique:
            result = set(result)
        if strip_placeholders:
            temp = [self._strip_non_ascii_chars(value) for value in result]
            return [value for value in temp if self._without_params(value)]
        else:
            return [self._strip_non_ascii_chars(value) for value in result]


class HtmlUrlExtractor(TextUrlExtractor):
    def __init__(self, root_url='', skip_images=False, **kwargs):
        self.root_url = root_url
        self.skip_images = skip_images

    def _validate_email(self, email):
        if len(email) > 7:
            if re.match('^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$', email):
                return True
        return False

    def _extract_from_anchors(self, soup):
        return {a.get('href') or a.text for a in soup.find_all('a')}

    def _extract_from_img(self, soup):
        if self.skip_images:
            return set()
        return {img.get('src') for img in soup.find_all('img')}

    def _fix_url(self, url):
        result = ''
        url_parsed = urlparse(url)
        if url_parsed.geturl().startswith('/'):
            if self.root_url:
                result = urljoin(self.root_url, url_parsed.geturl())
        elif url_parsed.scheme in ['http', 'https']:
            if re.match(self.url_pattern, url_parsed.geturl()):
                result = url_parsed.geturl()
        elif not url_parsed.scheme:
            if not self._validate_email(url_parsed.geturl()):
                full_url = 'http://' + url_parsed.geturl()
                if re.match(self.url_pattern, full_url):
                    result = full_url
        else:
            logging.error(f'{url_parsed.geturl()} not tested')
        return result

    def extract_urls(self, content, keep_placeholders=False):
        result = []
        soup = BeautifulSoup(content, 'lxml')
        urls = self._extract_from_anchors(soup) | self._extract_from_img(soup)
        for url in urls:
            fixed_url = self._fix_url(url)
            if fixed_url and (self._without_params(fixed_url) or keep_placeholders):
                result.append(fixed_url)
        return result


class UrlStatusChecker:
    retry_max_count = 3

    def __init__(self, headers=None, exclude_urls_regexs: list[str] | None = None):
        self._exclude_urls_regex = exclude_urls_regexs or []
        if self._exclude_urls_regex:
            logging.warning(f'Excluded urls regexps: {self._exclude_urls_regex}')
        self._headers = headers or {}
        if 'User-Agent' not in self._headers:
            self._headers['User-Agent'] = DEFAULT_USER_AGENT

    async def _make_request(self, url):
        try:
            logging.info(f'checking {url}')
            async with aiohttp.request('get', url, headers=self._headers, allow_redirects=True) as res:
                return res.status
        except Exception:
            logging.error('Error making request to %s', url)
            return 500

    async def _retry_request(self, url, status):
        new_status = status
        times = 1
        while times < self.retry_max_count and status == new_status:
            new_status = await self._make_request(url)
            times = times + 1
        return new_status

    async def _request_status_code(self, url):
        status = await self._make_request(url)
        if status == 500:
            return await self._retry_request(url, status)
        return status

    def _has_disallowed_chars(self, url):
        return url.find('\u200e') != -1

    def _is_valid(self, status_code, has_disallowed_chars):
        return (200 <= status_code < 300) and not has_disallowed_chars

    async def _check_urls_coro(self, urls, future):
        urls_without_excluded = []
        for url in urls:
            is_exluded = any(re.match(regex, url.url) for regex in self._exclude_urls_regex)
            if not is_exluded:
                urls_without_excluded.append(url)
            else:
                logging.warning(f'url {url.url} excluded from status check')
        tasks = [self._request_status_code(url.url) for url in urls_without_excluded]
        results = await asyncio.gather(*tasks)
        for index, url in enumerate(urls_without_excluded):
            url.status_code = results[index]
            url.has_disallowed_chars = self._has_disallowed_chars(url.url)
        invalid_urls = filter(lambda u: not u.is_valid(), urls)
        future.set_result(list(invalid_urls))

    def check(self, urls):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        future = asyncio.Future()
        loop.run_until_complete(self._check_urls_coro(urls, future))
        loop.close()

        return future.result()

    async def async_check(self, urls):
        future = asyncio.Future()
        await self._check_urls_coro(urls, future)
        return future.result()


class UrlValidator:
    _extractors = {'txt': TextUrlExtractor, 'html': HtmlUrlExtractor}

    def __init__(self, filetype, headers=None, exclude_status_check_regexs: list[str] | None = None, **kwargs):
        self.client_headers = headers or {}
        self._excluded_status_check_regexs = exclude_status_check_regexs or []
        extractor_class = self._extractors.get(filetype)
        if extractor_class is None:
            raise MissingUrlExtractorError('no extractor for filetype %s', filetype)
        self.extractor = extractor_class(**kwargs)

    def _get_urls(self, data, parser, reader):
        flat_data = {p for sublist in data for p in sublist}
        # TODO yield instead
        urls = {}
        for element in flat_data:
            content = parser.parse(reader.read(element))
            file_urls = self.extractor.extract_urls(content)
            for file_url in file_urls:
                url = urls.get(file_url, UrlDiff(file_url))
                url.add_file(element)
                urls[url.url] = url
        return urls

    def check(self, data, parser, reader):
        urls = self._get_urls(data, parser, reader)
        checker = UrlStatusChecker(headers=self.client_headers, exclude_urls_regexs=self._excluded_status_check_regexs)
        invalid_urls = checker.check(urls.values())
        return invalid_urls

    async def async_check(self, data, parser, reader):
        urls = self._get_urls(data, parser, reader)
        checker = UrlStatusChecker(headers=self.client_headers, exclude_urls_regexs=self._excluded_status_check_regexs)
        invalid_urls = await checker.async_check(urls.values())
        return invalid_urls


class UrlOccurenciesValidator(UrlValidator):
    def check(self, data, parser, reader):
        error = []
        for row in data:
            base = row.pop(0)
            base_urls = self._get_urls([[base]], parser, reader)
            for other in row:
                other_urls = self._get_urls([[other]], parser, reader)
                error.append(UrlOccurencyDiff(base, other, base_urls, other_urls))
        return [x for x in error if not x.is_valid()]

    def async_check(self, *args):
        raise NotImplementedError
