import unittest
import sys
import os
sys.path.insert(1, '../')
from Download_files import *

class MyTestCase(unittest.TestCase):

    def test_if_download_started(self):
        paths = os.path.join('data', 'test.zip')
        outfolder = os.path.join('data')
        files = unzip(paths, outfolder)
        assert len(files) == 1

if __name__ == '__main__':
    unittest.main()
