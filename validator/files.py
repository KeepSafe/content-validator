import os
import glob

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
        for f in glob.iglob(pattern):
            yield [f]

#
#
# def _langs(pattern, directory, lang):
#     split_dirs = pattern.split('{')
#     full_pattern = os.path.join(directory, split_dirs[0])
#     langs = [d for d in os.listdir(full_pattern) if not d.startswith('.') and d != lang]
#     langs.append(lang)
#     return langs
#
#
# def _file_for_langs(file_pattern, langs):
#     return [file_pattern.format(lang=lang) for lang in langs]
#
#
# def _resolve_patterns(directory, pattern, param_idx, lang):
#     pattern_bits = pattern.split('/')
#     common_path = os.path.join(*[p for p in pattern_bits[:param_idx]])
#     param_element = pattern_bits[param_idx]
#     common_with_param_length = len(os.path.join(common_path, lang))
#     files = glob.iglob(pattern.format(lang=lang))
#     patterns = [os.path.join(directory, common_path, param_element, f[common_with_param_length:].strip('/')) for f in files]
#     return patterns
#
#
# def files(pattern='*', directory=None, lang='en-US'):
#     if directory is None:
#         directory = os.getcwd()
#
#     param_idxs = [idx for idx, e in enumerate(pattern.split('/')) if lang_param in e]
#     print('aaaaa')
#     print(param_idxs)
#     if param_idxs:
#         #TODO improve for many
#         patterns = _resolve_patterns(pattern, param_idxs[0], lang)
#     else:
#         patterns = [pattern]
#     langs = _langs(pattern, directory, lang)
#     for file_pattern in patterns:
#         yield _file_for_langs(file_pattern, langs)
