class Url(object):
    def __init__(self, url):
        self.url = url
        self.files = []
        self.status_code = 200
        
    def __str__(self):
        return self.__repr__()
        
    def __repr__(self):
        return 'Url: %s' % self.url
        
    def is_valid(self):
        return 200 <= self.status_code < 300
        
    def add_file(self, path):
        self.files.append(path)
        
class HtmlDiff(object):
    def __init__(self, base_path, base, other_path, other, diff):
        self.base_path = base_path
        self.base = base
        self.other_path = other_path
        self.other = other
        self.diff = diff
        