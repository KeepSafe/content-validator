import re
import logging
import asyncio
import aiohttp
import string
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

from ..errors import UrlDiff

logging.getLogger('aiohttp').setLevel(logging.ERROR)
logging.getLogger('asyncio').setLevel(logging.ERROR)

DEFAULT_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/537.36 (KHTML, like Gecko)'\
                     'Chrome/54.0.2806.0 Safari/537.36'


class MissingUrlExtractorError(Exception):
    pass


class TextUrlExtractor(object):
    def __init__(self, **kwargs):
        pass

    url_pattern = r'(?i)\b((?:https?://|www\d{0,3}[.]|(!keepsafe://)[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()\[\]<>]' \
        '+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[' \
        '\];:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019]))'

    def _without_params(self, url):
        return not bool(re.search(r'\{\{[a-zA-Z0-9_.]+\}\}', url))

    def _strip_non_ascii_chars(self, url):
        return ''.join(filter(lambda c: c in string.printable, url))

    def extract_urls(self, content):
        result = set(match.group().strip(').') for match in re.finditer(self.url_pattern, content))
        return filter(self._without_params, map(self._strip_non_ascii_chars, result))


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
        return set([a.get('href') or a.text for a in soup.find_all('a')])

    def _extract_from_img(self, soup):
        if self.skip_images:
            return set()
        return set([img.get('src') for img in soup.find_all('img')])

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
            logging.error('{} not tested'.format(url_parsed.geturl()))
        return result

    def extract_urls(self, content):
        result = []
        soup = BeautifulSoup(content, 'lxml')
        urls = self._extract_from_anchors(soup) | self._extract_from_img(soup)
        for url in urls:
            fixed_url = self._fix_url(url)
            if fixed_url and self._without_params(fixed_url):
                result.append(fixed_url)
        return result


class UrlStatusChecker(object):
    retry_max_count = 3

    def __init__(self, headers=None):
        self._headers = headers or {}
        if 'User-Agent' not in self._headers:
            self._headers['User-Agent'] = DEFAULT_USER_AGENT

    async def _make_request(self, url):
        res = None
        try:
            logging.info('checking {}'.format(url))
            res = await aiohttp.request('get', url, headers=self._headers)
            return res.status
        except Exception:
            logging.error('Error making request to %s', url)
            return 500
        finally:
            if res:
                res.close()

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
        tasks = [self._request_status_code(url.url) for url in urls]
        results = await asyncio.gather(*tasks)
        for index, url in enumerate(urls):
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


class UrlValidator(object):
    _extractors = {'txt': TextUrlExtractor, 'html': HtmlUrlExtractor}

    def __init__(self, filetype, headers={}, **kwargs):
        self.client_headers = headers
        extractor_class = self._extractors.get(filetype)
        if extractor_class is None:
            raise MissingUrlExtractorError('no extractor for filetype %s', filetype)
        self.extractor = extractor_class(**kwargs)

    def _get_urls(self, data, parser, reader):
        flat_data = set(p for sublist in data for p in sublist)
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
        checker = UrlStatusChecker(headers=self.client_headers)
        invalid_urls = checker.check(urls.values())
        return invalid_urls

    async def async_check(self, data, parser, reader):
        urls = self._get_urls(data, parser, reader)
        checker = UrlStatusChecker(headers=self.client_headers)
        invalid_urls = await checker.async_check(urls.values())
        return invalid_urls
