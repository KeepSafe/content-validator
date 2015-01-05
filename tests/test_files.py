from unittest import TestCase
from unittest.mock import patch

from validator.files import files
from validator.utils import FileFormat


class TestFiles(TestCase):

    @patch('os.listdir')
    @patch('glob.iglob')
    def _test_files_happy_path(self, mock_iglob, mock_listdir):
        mock_listdir.return_value = ['en']
        mock_iglob.return_value = iter(['src/en/file1.md'])
        actual = files('src/{lang}/*.md', directory='', lang='en')

        self.assertEqual([1], mock_iglob.call_args_list)
