import itertools

class BaseError(object):

    def __init__(self):
        self.errors = []

    def __bool__(self):
        return len(self.errors) > 0

    def add_error(self, error):
        self.errors.append(error)

    def __str__(self):
        return '\n'.join([str(error) for error in self.errors])


class ContentError(BaseError):

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def __str__(self):
        msg = 'Errors for file {}\n'.format(self.file_path)
        msg = msg + super().__str__()
        return msg


class LinkError(object):

    def __init__(self, url, status_code):
        self.url = url
        self.status_code = status_code

    def __str__(self):
        return '\t{} returned status code {}'.format(self.url, self.status_code)


class CompareError(BaseError):

    def __init__(self, base_file_path, other_file_path):
        super().__init__()
        self.base_file_path = base_file_path
        self.other_file_path = other_file_path

    def __str__(self):
        msg = 'Errors for files comparison between base file {} and other file {}\n'.format(
            self.base_file_path, self.other_file_path)
        msg = msg + super().__str__()
        return msg


class TagsCountError(object):

    def __init__(self, base_tag_count, other_tag_count):
        self.base_tag_count = base_tag_count
        self.other_tag_count = other_tag_count

    def __str__(self):
        return '\tbase file has {} tags while other file has {} tags'.format(self.base_tag_count, self.other_tag_count)


class TagNameError(object):
    def __init__(self, base_tag_name, other_tag_name):
        self.base_tag_name = base_tag_name
        self.other_tag_name = other_tag_name

    def __str__(self):
        return '\tbase file has {} tag while other file has {} tag in that place'.format(self.base_tag_name, self.other_tag_name)


class MissingFileError(object):
    def __init__(self, file_path):
        self.file_path = file_path

    def __str__(self):
        return '\t{} file is missing'.format(self.file_path)

class ValidationError(object):
    def __init__(self):
        self.content_errors = []
        self.compare_errors = []

    @property
    def errors(self):
        return itertools.chain(self.content_errors, self.compare_errors)

    def __bool__(self):
        return len(self.content_errors) > 0 or len(self.compare_errors) > 0

    def add_content_error(self, error):
        self.content_errors.append(error)

    def add_compare_error(self, error):
        self.compare_errors.append(error)
