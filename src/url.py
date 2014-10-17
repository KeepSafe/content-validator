import requests
import re
import os
import sys
import logging

import utils

URL_PATTERN = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
URLS_DELIMITER = '=>'


def _print_and_flush(msg, **kwargs):
    print(msg, **kwargs)
    sys.stdout.flush()


def _make_request(url):
    try:
        return requests.get(url).status_code
    except requests.exceptions.ConnectionError as e:
        logging.error(e)
        return 500


def _retry_request(url, times=2, status=500):
    new_status = -1
    while times > 0 or status != new_status:
        _print_and_flush('retrying ' + url, end=' ')
        new_status = _make_request(url)
        if 200 <= new_status < 300:
            _print_and_flush('OK')
        else:
            _print_and_flush('FAIL')
        times = times - 1
    return 200 <= new_status < 300


def _is_url_valid(url):
    _print_and_flush('checking ' + url, end=' ')
    status = _make_request(url)
    if 200 <= status < 300:
        _print_and_flush('OK')
        return True
    if status == 500:
        _print_and_flush('FAIL')
        return _retry_request(url)
    _print_and_flush('FAIL')
    return False


def _urls_from_content(content):
    return {match.group() for match in re.finditer(URL_PATTERN, content)}


def _filter_invalid_urls(urls):
    return {url for url in urls if not _is_url_valid(url)}


def _save_invalid_urls(urls, root_folder, output_file):
    filepath = os.path.join(root_folder, output_file)
    with open(filepath, 'w') as fp:
        fp.writelines(url + '\n' for url in urls)


def _read_replace_values(root_folder, input_file):
    values = {}
    content = utils.file_content(root_folder, input_file)
    for line in content.splitlines():
        if URLS_DELIMITER in line:
            old_url, new_url = line.split(URLS_DELIMITER)
            values[old_url.strip()] = new_url.strip()
    if not values:
        raise ValueError('no mapping found, nothing will happen. please check the docs to get a valid mapping example')
    return values


def _replace_values_in_content(content, values_mapping):
    for old_url, new_url in values_mapping.items():
        content = re.sub(re.escape(old_url), new_url, content)
    return content


def _fix_invalid_links(root_folder, files, input_file):
    values_mapping = _read_replace_values(root_folder, input_file)
    for filename in files:
        content = utils.file_content(root_folder, filename)
        content = _replace_values_in_content(content, values_mapping)
        with open(os.path.join(root_folder, filename), 'w') as fp:
            fp.write(content)


def _find_invalid_links(root_folder, files, output_file):
    invalid_urls = set()
    for content in utils.files_content(root_folder, files):
        urls = _urls_from_content(content)
        invalid_urls = invalid_urls.union(_filter_invalid_urls(urls))
    if invalid_urls and output_file:
        _save_invalid_urls(invalid_urls, root_folder, output_file)


def validate_content(args):
    files = args['files']
    root_folder = args['root_folder']
    output_file = args['output_file']
    input_file = args['input_file']
    if output_file and input_file:
        raise ValueError('Can\'t both define input and output file')
    if input_file:
        _fix_invalid_links(root_folder, files, input_file)
    else:
        _find_invalid_links(root_folder, files, output_file)
