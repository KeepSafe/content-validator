import argparse
import os
import logging

from . import url

DEFAULE_LOG_LEVEL = 'WARNING'


def parse_args():
    parser = argparse.ArgumentParser(epilog='Brought to you by KeepSafe - www.getkeepsafe.com')

    # Global settings
    parser.add_argument('-l', '--loglevel',
                        help='Specify log level (DEBUG, INFO, WARNING, ERROR, CRITICAL), default: %s'
                        % DEFAULE_LOG_LEVEL,
                        default=DEFAULE_LOG_LEVEL)
    parser.add_argument('-o', '--output-file', help='Save output to a file')
    parser.add_argument('-i', '--input-file', help='Use input from a file to replace missing links')
    parser.add_argument('-f', '--filter', help='File name filter pattern', default='*')
    parser.add_argument('root_folder', help='Root folder to search in')

    args = parser.parse_args()
    return vars(args)


def validate_args(args):
    assert os.path.isdir(args['root_folder']), 'provided path needs to be a folder'
    if args['input_file']:
        assert os.path.isfile(args['input_file']), 'input file needs to be a file'


def main():
    args = parse_args()
    validate_args(args)
    init_log(args['loglevel'])
    invalid_urls = url.validate_content(args)


def init_log(loglevel):
    num_level = getattr(logging, loglevel.upper(), 'WARNING')
    logging.basicConfig(level=num_level)


if __name__ == '__main__':
    main()
