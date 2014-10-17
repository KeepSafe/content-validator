import os


def files_content(root_folder, files):
    for filename in files:
        filepath = os.path.join(root_folder, filename)
        if os.path.isfile(filepath):
            with open(filepath) as fp:
                yield fp.read()
