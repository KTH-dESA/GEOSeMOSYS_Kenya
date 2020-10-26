import unittest
import sys
sys.path.insert(1, '../')
from Download_files import *

class MyTestCase(unittest.TestCase):

    def test_if_download_started(self):
        paths = 'test_download.txt'
        files = download_unzip_data(paths)
        assert len(files) == 19

if __name__ == '__main__':
    unittest.main()
