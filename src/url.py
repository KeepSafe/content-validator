import requests
import re
import os

URL_PATTERN = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
URLS_FILENAME = 'invalid_urls.txt'


def _retry_request(url, times=2, status=500):
    new_status = -1
    while times > 0 or status != new_status:
        print('retrying ' + url)
        new_status = requests.get(url).status_code
        times = times - 1


def _is_url_valid(url):
    print('checking ' + url)
    res = requests.get(url)
    status = res.status_code
    if 200 <= status < 300:
        return True
    if status == 500:
        return _retry_request(url)
    return False


def _urls_from_content(content):
    return {match.group() for match in re.finditer(URL_PATTERN, content)}


def _filter_invalid_urls(urls):
    return {url for url in urls if _is_url_valid(url)}


def _save_invalid_urls(urls, options):
    root_folder = options['root_folder']
    filepath = os.path.join(root_folder, URLS_FILENAME)
    with open(filepath, 'w') as fp:
        for url in urls:
            fp.write(url)


def validate_content(content, options):
    urls = _urls_from_content(content)
    invalid_urls = _filter_invalid_urls(urls)
    _save_invalid_urls(invalid_urls, options)
