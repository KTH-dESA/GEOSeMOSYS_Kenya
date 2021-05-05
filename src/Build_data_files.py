import pandas as pd
import geopandas
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

    solarbase.to_csv('../data/capacityfactor_solar.csv')

    header = windbase.columns
    new_header = [x.replace('X','') for x in header]
    windbase.columns = new_header
    windbase.drop('Unnamed: 0', axis='columns', inplace=True)
    GIS_col = windbase.columns

    solarbase.to_csv('../data/capacityfactor_wind.csv')

    GIS = pd.DataFrame(range(1,379), columns = ['Location'])
    #GIS.sort_values(by='Location')
    print(GIS)
    GIS.to_csv('../data/GIS_data.csv')

    return()


if __name__ == "__main__":
    path = sys.argv[1]

    renewableninja(path)
