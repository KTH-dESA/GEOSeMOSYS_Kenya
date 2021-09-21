# Runs all the GIS-steps for the Facebook developed Pathfinder https://github.com/facebookresearch/many-to-many-dijkstra
#
# Author: Nandi Moksnes
# Date: 16 September 2021
# Python version: 3.8

import os
import sys
os.chdir('..')
from Pathfinder_GIS_steps import *
from Pathfinder import *
import numpy as np
import pandas as pd

os.chdir('src')

path = '../Projected_files/'
proj_path = 'temp'
elec_shp = '../Projected_files/elec.shp'
#elec_shape = '../Projected_files/zero_to_one_elec.shp'
roads = os.path.join(path, 'UMT37S_Roads.shp')  # the road shape file
dijkstrapath = 'temp/dijkstra/road_3761.tif'
dijkstra_weight = "../Projected_files/dijkstraweight.shp"
pop_cutoff= 10

#Only settlements with population over 20 are concidered to be part of the distribution network
elec_shape = convert_zero_to_one(elec_shp, pop_cutoff)
#The elec_raster will serve as the points to connect and the roads will create the weights
#Returns the path to elec_raster
elec_raster = rasterize_elec(elec_shape, path)

#Concatinate the highway with high- medium and low voltage lines
#dijkstra_weight = merge_road_grid(path)

#returns the path to highway_weights

#highway_shp = highway_weights(dijkstra_weight, path)
#highway_shp =  "../Projected_files/highways_weights.shp"
#highway_raster = rasterize_road(highway_shp, path)
highway_raster = "../Projected_files/weights.tif"
#elec_raster = "../Projected_files/zero_to_one_elec.tif"
#clip the rasters to spatial dimension defined in src/temp
files = os.listdir(proj_path)
shapefiles = []
for file in files:
    if file.endswith('.shp'):
        f = os.path.join('temp/', file)
        shapefiles += [f]

for f in shapefiles:
    name, end = os.path.splitext(os.path.basename(f))
    #clip
    weight_raster = masking(f, highway_raster, '%s_w.tif' %(name))
    weight_csv = make_weight_numpyarray(weight_raster, name)
    #make csv files for Dijkstra
    elec_ = masking(f, elec_raster,  '%s_e.tif' %(name))
    target_csv = make_target_numpyarray(elec_, name)
    targets = np.genfromtxt(os.path.join('temp/dijkstra', "%s_target.csv" %(name)), delimiter=',')
    if np.count_nonzero(targets) != 0:
        weights = np.genfromtxt(os.path.join('temp/dijkstra', "%s_weight.csv" %(name)), delimiter=',')
        origin_csv = make_origin_numpyarray(target_csv, name)
        origin = np.genfromtxt(os.path.join('temp/dijkstra', "%s_origin.csv" %(name)), delimiter=',')
        # Run the Pathfinder alogrithm seek(origins, target, weights, path_handling='link', debug=False, film=False)
        print("Calculating Pathfinder")
        pathfinder = seek(origin, targets, weights, path_handling='link', debug=False, film=False)

        elec_path = pathfinder['paths']
        pd.DataFrame(elec_path).to_csv("temp/dijkstra/elec_path_%s.csv" %(name))
        distance_path = pathfinder['distance']
        pd.DataFrame(distance_path).to_csv("temp/dijkstra/distance_path_%s.csv" %(name))
        rendering_path = pathfinder['rendering']
        pd.DataFrame(rendering_path).to_csv("temp/dijkstra/rendering_path_%s.csv" %(name))
        print("Saving results to csv from Pathfinder")
        # print the algortihm to raster
        print("Converting results from Pathfinder to raster")
        raster_pathfinder = make_raster(elec_path, name)