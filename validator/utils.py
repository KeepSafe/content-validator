import os
from enum import Enum


# TODO move to a better place
class FileFormat(Enum):
    md = 1
    xml = 2


def file_content(root_folder, filename):
    filepath = os.path.join(root_folder, filename)
    if os.path.isfile(filepath):
        with open(filepath) as fp:
            return fp.read()


def save_seq_to_file(urls, filepath):
    with open(filepath, 'w') as fp:
        fp.writelines(url + '\n' for url in urls)
