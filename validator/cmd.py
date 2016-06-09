"""
Handles command line and calls the email parser with corrent options.
"""

import argparse
import logging
from collections import namedtuple

logger = logging.getLogger()

Settings = namedtuple('Settings', [
    'source',
    'base_locale',
    'output',
    'verbose'
])


def default_settings():
    return Settings(
        source='src/{lang}/*.xml',
        base_locale='en',
        output='errors/summary.html',
        verbose=False
    )


def read_args(argsargs=argparse.ArgumentParser):
    settings = default_settings()
    logger.debug('reading arguments list')
    args = argsargs(epilog='Brought to you by KeepSafe - www.getkeepsafe.com')

    args.add_argument('-s', '--source', help='args\'s source folder, default: %s' % settings.source)
    args.add_argument('-o', '--output',
                      help='destination path for HTML report, default: %s' % settings.output)
    args.add_argument('-l', '--base-locale', help='Base locale for comparision: %s' % settings.base_locale)
    args.add_argument('-vv', '--verbose', help='Verbose', action='store_true')
    args.add_argument('-v', '--version', help='Show version', action='store_true')
    return args.parse_args()


def read_settings(args):
    args = vars(args)
    settings = default_settings()._asdict()
    for k in settings:
        if k in args and args[k] is not None:
            settings[k] = args[k]
    return Settings(**settings)


def print_version():
    import pkg_resources
    version = pkg_resources.require('content-validator')[0].version
    print(version)
    return True
