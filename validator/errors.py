from collections import namedtuple


class UrlDiff(object):

    def __init__(self, url, files=None, status_code=200, has_disallowed_chars=False):
        self.url = url
        self.files = files or []
        self.status_code = status_code
        self.has_disallowed_chars = has_disallowed_chars

    def __str__(self):
        return 'Url(%s, %s, %s, %s)' % (self.url, self.files, self.status_code, self.has_disallowed_chars)

    def __repr__(self):
        return 'Url: %s' % self.url

    def is_valid(self):
        return 200 <= self.status_code < 300 and not self.has_disallowed_chars

    def add_file(self, path):
        self.files.append(path)


class UrlOccurencyDiff:
    def __init__(self, url, base_file, translated_file, base_urls, translation_urls):
        # DONE - DD
        # it's up to you how you implement this, don't suggest too much with below preposition
        self.url = url
        self.base_path = base_file
        self.translation_path = translated_file
        self.base_occurencies = base_urls
        self.translation_occurencies = translation_urls

    def is_valid(self):
        return self.base_occurencies == self.translation_occurencies



ContentData = namedtuple('ContentData', ['original', 'parsed', 'diff', 'html'])
ContentData.__new__.__defaults__ = ('', ) * 2


class MdDiff(object):

    def __init__(self, base, other, error_msgs):
        self.base = base
        self.other = other
        self.error_msgs = error_msgs
