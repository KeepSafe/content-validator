class ContentError(object):
    def __init__(self, path, suberrors):
        self.path = path
        self.suberrors = suberrors

    def __str__(self):
        message = 'the content of {} has errors:\n'.format(self.path)
        for error in self.suberrors:
            message = message + str(error) + '\n'
        return message

class ComparisonError(object):

    def __init__(self, base_path, other_path, suberrors):
        self.base_path = base_path
        self.other_path = other_path
        self.suberrors = suberrors

    def __str__(self):
        message = 'the content of {} is not the same as {}:\n'.format(self.base_path, self.other_path)
        for error in self.suberrors:
            message = message + str(error) + '\n'
        return message

class UrlError(object):

    def __init__(self, url, status_code):
        self.url = url
        self.status_code = status_code

    def __str__(self):
        return '{} returned status code {}'.format(self.url, self.status_code)

class MarkdownError(object):

    def __init__(self, base, other):
        self.base = base
        self.other = other

    def __str__(self):
        return 'markdown error'
