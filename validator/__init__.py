from .files import Files
from .utils import FileFormat


def validator(file_format):
    return Files(file_format)
