from collections import namedtuple


class UrlDiff(object):

    def __init__(self, url, files=None, status_code=200):
        self.url = url
        self.files = files or []
        self.status_code = status_code

    def __str__(self):
        return 'Url(%s, %s, %s)' % (self.url, self.files, self.status_code)

    def __repr__(self):
        return 'Url: %s' % self.url

    def is_valid(self):
        return 200 <= self.status_code < 300

    def add_file(self, path):
        self.files.append(path)


ContentData = namedtuple('ContentData', ['original', 'parsed', 'diff'])


class MdDiff(object):

    def __init__(self, base, other, error_msgs):
        self.base = base
        self.other = other
        self.error_msgs = error_msgs
