# This script downloads data that is required for the analysis and unzips them
# Developed by Nandi Moksnes 2020-12 for the paper GEOSeMOSYS

from urllib.request import Request, urlopen
import shutil
import zipfile
import tarfile
import os
import pandas as pd
import sys

def download_url_data(url,temp):
    url_adress = pd.read_csv(url, header=None, sep=',')
    for i, row in url_adress.iterrows():
        req = Request(row[0], headers={'User-Agent': 'Chrome'})
        with urlopen(req) as response, open("%s/%s" % (temp, row[1]), 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
    return()

def unzip_all(url):
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
            unzip(os.path.join('temp', row[1]), os.path.join('GIS_data', name))
        elif ending == '.tgz':
            extract(os.path.join('temp', row[1]), os.path.join('GIS_data', name))
        else:
            shutil.copy(os.path.join('temp', row[1]), os.path.join('GIS_data', row[1]))

if __name__ == "__main__":
    current = os.getcwd()
    url_adress,temp = sys.argv[1], sys.argv[2]
    download = download_url_data(url_adress, temp)
    unzip = unzip_all(url_adress)

