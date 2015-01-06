import os
import glob
from pathlib import Path

from .parser import parser
from .utils import FileFormat


lang_param = '{lang}'


def _langs(pattern, directory, lang):
    split_dirs = pattern.split('{')
    full_pattern = os.path.join(directory, split_dirs[0])
    langs = [d for d in os.listdir(full_pattern) if not d.startswith('.') and d != lang]
    langs.append(lang)
    return langs


def _file_patterns(pattern, directory, lang):
    lang_pattern = os.path.join(directory, pattern.format(lang=lang))
    files = glob.iglob(lang_pattern)
    return (f[len(directory):].replace('/{}/'.format(lang), '/{{{}}}/'.format('lang')).strip('/') for f in files)

def _file_for_langs(file_pattern, langs):
    return [file_pattern.format(lang=lang) for lang in langs]


def files(pattern='*', directory=None, lang='en-US'):
    directory = directory or os.getcwd()

    if lang_param in pattern:
        langs = _langs(pattern, directory, lang)
        file_patterns = _file_patterns(pattern, directory, lang)
        for file_pattern in file_patterns:
            yield _file_for_langs(file_pattern, langs)
    else:
        for f in Path(directory).glob(pattern):
            yield [str(f)]
