import os


def files_content(root_folder, files):
    for filename in files:
        yield file_content(root_folder, filename)


def file_content(root_folder, filename):
    filepath = os.path.join(root_folder, filename)
    if os.path.isfile(filepath):
        with open(filepath) as fp:
            return fp.read()
