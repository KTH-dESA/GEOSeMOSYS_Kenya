import pandas as pd
import geopandas as gpd
import sys
import os
import fnmatch

def renewableninja(path):
    files = os.listdir(path)
    outwind = []
    outsolar = []
    for file in files:
        if fnmatch.fnmatch(file, '*out_wind*'):
            file = os.path.join(path,file)
            wind = pd.read_csv(file, index_col='time')
            outwind.append(wind)
    for file in files:
        if fnmatch.fnmatch(file, '*out_solar*'):
            file = os.path.join(path,file)
            solar = pd.read_csv(file, index_col='time')
            outsolar.append(solar)

    solarbase = pd.concat(outsolar, axis=1)
    windbase = pd.concat(outwind, axis=1)

    header = solarbase.columns
    new_header = [x.replace('X','') for x in header]
    solarbase.columns = new_header

    solarbase.drop('Unnamed: 0', axis='columns', inplace=True)
    solarbase.to_csv('run/data/capacityfactor_solar.csv')

    header = windbase.columns
    new_header = [x.replace('X','') for x in header]
    windbase.columns = new_header
    windbase.drop('Unnamed: 0', axis='columns', inplace=True)
    windbase.to_csv('run/data/capacityfactor_wind.csv')
    return()

def GIS_file():
    point = gpd.read_file('../Projected_files/new_40x40points_WGSUMT37S.shp')
    GIS_data = point['pointid']
    grid = pd.DataFrame(GIS_data, copy=True)
    grid.columns = ['Location']
    grid.to_csv('run/data/GIS_data.csv', index=False)
    return()

if __name__ == "__main__":
    path = sys.argv[1]
    renewableninja(path)
    GIS_file()
