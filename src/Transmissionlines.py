"""
Module: Transmissionlines
=============================

A module for calculating the transmissionlines distance from un-electrified points
----------------------------------------------------------------------------------------------------------------

Module author: Nandi Moksnes <nandi@kth.se>

"""
import geopandas as gpd
import pandas as pd
from geopandas.tools import sjoin
import os
def near_dist(pop_shp, un_elec_cells, path):

    unelec = pd.read_csv(un_elec_cells, header=None)
    point = gpd.read_file(os.path.join(path, pop_shp))
    point.index = point['pointid']
    unelec_shp = gpd.GeoDataFrame()
    for i in unelec[0]:
        unelec_point = point.loc[i]
        unelec_shp = unelec_shp.append(unelec_point)

    lines = gpd.read_file(os.path.join(path, 'Concat_Transmission_lines_UMT37S.shp'))

    unelec_shp['Transmission'] = unelec_shp.geometry.apply(lambda x: lines.distance(x).min())

    unelec_shp.to_file("run/Demand/transmission.shp", crs= point.crs)

def capital_cost_transmission_distrib(transmission_near):

    return()

if __name__ == "__main__":
    pop_shp = 'new_40x40points_WGSUMT37S.shp'
    transmission_near = "run/Demand/transmission.shp"
    un_elec_cells = 'run/un_elec_cells.csv'
    Projected_files_path = '../Projected_files/'
    near_dist(pop_shp, un_elec_cells, Projected_files_path)