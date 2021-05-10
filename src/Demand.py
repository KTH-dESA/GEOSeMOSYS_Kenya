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
    """

    :param elec:
    :param tif:
    :param cells:
    :return:
    """
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
    if not os.path.exists('run/Demand'):
        os.makedirs('run/Demand')
    demand_cell.to_csv('run/Demand/demand_cells.csv')
    path = 'run/Demand/demand_cells.csv'
    return(path)

def calculate_demand(settlements, path):
    demand_cell = pd.read_csv(settlements)
    demand_points = demand_cell.groupby("pointid_right")["elec"]
    demand_points.get_group(1)
    print(demand_points)

    return ()


if __name__ == "__main__":
    shape = '../Projected_files/new_40x40polygon_WGSUMT37S.shp'
    gdp = '../Projected_files/masked_UMT37S_GDP_PPP_Layer2015.tif'
    elec_shp = '../Projected_files/elec.shp'
    path = 'run/Demand'
    settlements = 'run/Demand/demand_cells.csv'
    #settlements = join(elec_shp, gdp, shape)
    demand = calculate_demand(settlements, path)




