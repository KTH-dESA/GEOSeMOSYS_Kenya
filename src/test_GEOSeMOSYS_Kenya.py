import unittest
from os import listdir
from os.path import isfile, join
from Download_files import *

class ImportTestCase(unittest.TestCase):
    def test_files_download_csvs_count_nr_loaded_zip_should_be_1(self):
        paths = os.path.join(os.getcwd(), 'test_data','test_download.txt')
        download_url_data(paths, 'test_data/temp')
        files = os.listdir(os.path.join(os.getcwd(),'../test_data/temp'))
        number = []
        for i in files:
            _, filename = os.path.split(i)
            name, ending = os.path.splitext(filename)
            number.append(ending)
        assert len(number) == 1

    # def test_unzip_should_be_5(self):
    #     path = os.path.join(os.path.normpath(os.getcwd() + os.sep + os.pardir), r'test_data\temp')
    #     unzip_all(os.path.join(os.getcwd(), 'test_data','test_download.txt'))
    #     onlyfiles = [f for f in listdir(path) if isfile(join(path, f))]
    #     assert len(onlyfiles) == 5

if __name__ == '__main__':
    unittest.main()

