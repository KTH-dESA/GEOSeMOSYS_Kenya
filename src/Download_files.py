"""
Module: Download_files
=============================

A module that downloads data that is required for the GEOSeMOSYS Kenya analysis and unzips them and places them in a new folder "GIS-data"
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Module author: Nandi Moksnes <nandi@kth.se>

"""

from urllib.request import Request, urlopen
import shutil
import zipfile
import tarfile
import os
import pandas as pd
import sys

def download_url_data(url,temp):
    """ This function downloads the data from URL in url (comma separated file) and place them in temp

    :param url:
    :param temp:
    :return:
    """

    def create_dir(dir):
        if not os.path.exists(dir):
            os.makedirs(dir)
    create_dir(('../' + temp))
    url_adress = pd.read_csv(url, header=None, sep=',')
    for i, row in url_adress.iterrows():
        req = Request(row[0], headers={'User-Agent': 'Chrome'})
        with urlopen(req) as response, open("../%s/%s" % (temp, row[1]), 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
    return()

def unzip_all(url):
    """ This function unzips the data from URL (url) and place them in GIS_data folder

    :param url:
    :return:
    """

    def create_dir(dir):
        if not os.path.exists(dir):
            os.makedirs(dir)
    create_dir(('../GIS_data'))
    url_adress = pd.read_csv(url, header=None, sep=',')
    def unzip(infolder, outfolder):
        with zipfile.ZipFile(infolder, 'r') as zip_ref:
            zip_ref.extractall(outfolder)
        return ()

    def extract(tar_url, out_path):
        tar = tarfile.open(tar_url, 'r')
        for item in tar:
            tar.extract(item, out_path)
            if item.name.find(".tgz") != -1 or item.name.find(".tar") != -1:

                extract(item.name, "./" + item.name[:item.name.rfind('/')])
    for i, row in url_adress.iterrows():
        _, filename = os.path.split(row[1])
        name, ending = os.path.splitext(filename)
        if ending == '.zip':
            unzip(os.path.join('../temp', row[1]), os.path.join('../GIS_data', name))
        elif ending == '.tgz':
            extract(os.path.join('../temp', row[1]), os.path.join('../GIS_data', name))
        else:
            shutil.copy(os.path.join('../temp', row[1]), os.path.join('../GIS_data', row[1]))

if __name__ == "__main__":
    current = os.getcwd()
    url_adress,temp = sys.argv[1], sys.argv[2]
    download = download_url_data(url_adress, temp)
    unzip = unzip_all(url_adress)

