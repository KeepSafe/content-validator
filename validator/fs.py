from pathlib import Path
from string import Formatter
from collections import defaultdict
from enum import Enum
import parse


class Filetype(Enum):
    txt = 0
    md = 1
    xml = 2


def read_content(path):
    with path.open() as fp:
        return fp.read()


def save_report(directory, source_path, report):
    path = Path(directory).joinpath(source_path.with_suffix('.html'))
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
    # extract named parameters from the pattern
    params = [p for p in map(lambda e: e[1], Formatter().parse(pattern)) if p]
    if params:
        if len(params - kwargs.keys()) > 0:
            raise ValueError('missing parameters {} for pattern {}'.format(params - kwargs.keys(), pattern))
        return _params_pattern(pattern, params, **kwargs)
    else:
        return _no_params_pattern(pattern)
