import argparse
import os
import logging

import url

DEFAULE_LOG_LEVEL = 'WARNING'


def parse_args():
    parser = argparse.ArgumentParser(epilog='Brought to you by KeepSafe - www.getkeepsafe.com')

    # Global settings
    parser.add_argument('-l', '--loglevel',
                        help='Specify log level (DEBUG, INFO, WARNING, ERROR, CRITICAL), default: %s'
                        % DEFAULE_LOG_LEVEL,
                        default=DEFAULE_LOG_LEVEL)
    parser.add_argument('-r', '--root-folder',
                        help='Root folder, default: .',
                        default=os.getcwd())
    parser.add_argument('-o', '--output-file', help='Save output to a file')
    parser.add_argument('-i', '--input-file', help='Use input from a file to replace missing links')
    parser.add_argument('files', help='File paterrn for filterning', nargs='*')

    args = parser.parse_args()
    return vars(args)


def main():
    args = parse_args()
    init_log(args['loglevel'])
    url.validate_content(args)


def init_log(loglevel):
    num_level = getattr(logging, loglevel.upper(), 'WARNING')
    logging.basicConfig(level=num_level)


if __name__ == '__main__':
    main()
