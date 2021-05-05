# Author: KTH dESA Last modified by Nandi Moksnes
# Date: 2021-05
# Python version: 3.8
import geopandas as gpd
from geopandas.tools import sjoin
import pandas as pd
import rasterio
from rasterio.merge import merge
from osgeo import gdal, ogr, gdalconst
import os

def join(elec, tif, cells):
    settlements = gpd.read_file(elec)
    print(settlements.crs)
    settlements.index = range(len(settlements))
    coords = [(x, y) for x, y in zip(settlements.geometry.x, settlements.geometry.y)]

    _, filename = os.path.split(tif)
    name, ending = os.path.splitext(filename)
    gdp = rasterio.open(tif)
    print(gdp.crs)
    settlements['GDP_PPP'] = [x[0] for x in gdp.sample(coords)]
    print(name)

    cell =  gpd.read_file(cells)
    demand_cells = sjoin(settlements, cell, how="left")
    demand_cell = pd.DataFrame(demand_cells, copy=True)
    print(demand_cell)
    return(demand_cell)

def calculate_demand(settlements, path):
    number_demand = settlements.groupby("elec")["pointid_right"].count()
    print(number_demand)



    return ()


if __name__ == "__main__":
    shape = '../Projected_files/new_40x40polygon_WGSUMT37S.shp'
    gdp = '../Projected_files/masked_UMT37S_GDP_PPP_Layer2015.tif'
    elec_shp = '../Projected_files/elec.shp'
    path = 'run/Demand'
    settlements = join(elec_shp, gdp, shape)
    demand = calculate_demand(settlements, path)




