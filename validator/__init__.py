import argparse
import os
import logging
from unittest import TestCase, defaultTestLoader, TextTestRunner

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
    if args['input_file'] and args['output_file']:
        raise ValueError('Can\'t both define input and output file')


def run_as_test(invalid_urls):
    class UrlTest(TestCase):
        def test_invelid_urls(self):
            self.assertEqual([], invalid_urls)
    suite = defaultTestLoader.loadTestsFromTestCase(UrlTest)
    TextTestRunner().run(suite)


def validate_content(args):
    root_folder = args['root_folder']
    output_file = args['output_file']
    input_file = args['input_file']
    pattern = args['filter']
    if input_file:
        url.fix_invalid_links(root_folder, input_file, pattern)
    else:
        invalid_links = url.find_invalid_links(root_folder, pattern)
        if output_file:
            filepath = os.path.join(root_folder, output_file)
            utils.save_seq_to_file(invalid_links, filepath)
        else:
            run_as_test(invalid_links)


def main():
    args = parse_args()
    validate_args(args)
    init_log(args['loglevel'])
    validate_content(args)


def init_log(loglevel):
    num_level = getattr(logging, loglevel.upper(), 'WARNING')
    logging.basicConfig(level=num_level)


if __name__ == '__main__':
    main()
