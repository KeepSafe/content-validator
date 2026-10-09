from pathlib import Path
from string import Formatter
from collections import defaultdict
import parse
import logging

logger = logging.getLogger(__name__)


def read_content(path):
    if path.exists():
        with path.open() as fp:
            return fp.read()
    else:
        logger.warn('%s does not exist', path.resolve())
        return ''


def save_report(directory, source_path, report):
    rel_path = Path(str(source_path).replace('../', ''))
    path = Path(directory).joinpath(rel_path.with_suffix('.html'))
    try:
        path.parent.mkdir(parents=True)
    except FileExistsError:
        pass
    with path.open('w') as fp:
        fp.write(report)


def _no_params_pattern(pattern):
    yield list(Path().glob(pattern))


def _get_param_values(pattern, paths):
    values = []
    wildcard_paths = set()
    parser = parse.compile(pattern)

    for path in paths:
        result = parser.parse(str(path))
        wildcard_paths.add(result.fixed)
        values.append(result.named)

    return values, wildcard_paths


def _params_pattern(pattern, params, **kwargs):
    files = defaultdict(list)

    # change parameters for wildcards so we can use it in glob
    wildcard_params = {k: '*' for k in params}
    wildcard_pattern = pattern.format(**wildcard_params)
    if Path(wildcard_pattern).is_absolute():
        rel_wildcard_pattern = str(Path(wildcard_pattern).relative_to('/'))
        paths = list(Path('/').glob(rel_wildcard_pattern))
    else:
        paths = list(Path().glob(wildcard_pattern))

    # get all available values for params and wildcards
    parse_pattern = pattern.replace('**', '{}').replace('*', '{}')
    param_values, wildcard_paths = _get_param_values(parse_pattern, paths)

    for wildcard_path in wildcard_paths:
        base_path = Path(parse_pattern.format(*wildcard_path, **kwargs))
        for values in param_values:
            other_path = Path(parse_pattern.format(*wildcard_path, **values))
            if other_path != base_path and other_path not in files[base_path]:
                files[base_path].append(other_path)

    for k, v in files.items():
        result = list(v)
        result.insert(0, k)
        yield result


def files(pattern, **kwargs):
    """
    Return list of list of `Path <https://docs.python.org/3/library/pathlib.html#pathlib.Path>`_ to
    files matching the pattern.
    In addition of the normal Path.glob syntax the pattern accepts parameters in a form of param ``{param}``.
    You need to pass a default parameter value for every parameter, path with the default will become the first
    Path in the list.

    Examples:

    explicit pattern: 'path/to/file.txt' will resolve [[Path(path/to/file.txt)]]
    wildcard pattern: 'path/to/*.txt' will resolve [[Path(path/to/file1.txt), Path(path/to/file2.txt)]]
    parameter pattern, default name=file1: 'path/to/{name}.txt' will resolve
    [[Path(path/to/file1.txt), Path(path/to/file2.txt)]]
    parameter wildcard pattern, default name=file1: 'path/*/{name}.txt' will resolve
    [[Path(path/to1/file1.txt), Path(path/to1/file2.txt)], [Path(path/to2/file1.txt), Path(path/to2/file2.txt)]]
    """
    # extract named parameters from the pattern
    params = {p for p in map(lambda e: e[1], Formatter().parse(pattern)) if p}
    if params:
        if len(params - kwargs.keys()) > 0:
            raise ValueError(f'missing parameters {params - kwargs.keys()} for pattern {pattern}')
        return _params_pattern(pattern, params, **kwargs)
    else:
        return _no_params_pattern(pattern)


def file(base_path, other_path):
    """
    Returns a single file
    """
    return [[Path(base_path), Path(other_path)]]
