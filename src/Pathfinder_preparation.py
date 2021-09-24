# Runs all the GIS-steps for the Facebook developed Pathfinder https://github.com/facebookresearch/many-to-many-dijkstra
#
# Author: Nandi Moksnes
# Date: 16 September 2021
# Python version: 3.8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import with_statement
import os
import sys

from Pathfinder_GIS_steps import *
from Pathfinder import *
import numpy as np
import pandas as pd

path = '../Projected_files/'
proj_path = 'temp'
elec_shp = '../Projected_files/elec.shp'
#elec_shape = '../Projected_files/zero_to_one_elec.shp'
dijkstra_weight = "../Projected_files/dijkstraweight.shp"
pop_cutoff= 20

#Only settlements with population over pop_cutoff are concidered to be part of the distribution network
#elec_shape = convert_zero_to_one(elec_shp, pop_cutoff)
#The elec_raster will serve as the points to connect and the roads will create the weights
#Returns the path to elec_raster
#elec_raster = rasterize_elec(elec_shape, path)

#Concatinate the highway with high- medium and low voltage lines
#grid_weight = merge_grid(path)

#returns the path to highway_weights

#highway_shp, grid_shp = highway_weights(grid_weight, path)
#highway_shp =  "../Projected_files/road_weights.shp"
#highway_raster = rasterize_road(highway_shp, path)
#grid_shp =  "../Projected_files/grid_weights.shp"
#transmission_raster = rasterize_transmission(grid_shp, path)
transmission_raster = "../Projected_files/transmission.tif"
highway_raster = "../Projected_files/road.tif"
weights_raster = merge_raster(transmission_raster, highway_raster)
#weights_raster = "../Projected_files/weights.tif"
elec_raster = "../Projected_files/zero_to_one_elec.tif"

print("Calculating Pathfinder for all of Kenya")
name = 'Kenya'
#makegrid_csv = make_weight_numpyarray(transmission_raster, 'grid')
weight_csv = make_weight_numpyarray(weights_raster, name)

#make csv files for Dijkstra
target_csv = make_target_numpyarray(elec_raster, name)
targets = np.genfromtxt(os.path.join('temp/dijkstra', "%s_target.csv" %(name)), delimiter=',')
weights = np.genfromtxt(os.path.join('temp/dijkstra', "%s_weight.csv" %(name)), delimiter=',')
origin_csv = make_origin_numpyarray(target_csv, name)
origin = np.genfromtxt(os.path.join('temp/dijkstra', "%s_origin.csv" %(name)), delimiter=',')
# Run the Pathfinder alogrithm seek(origins, target, weights, path_handling='link', debug=False, film=False)
print("Calculating Pathfinder")
pathfinder = seek(origin, targets, weights, path_handling='link', debug=False, film=False)
elec_path = pathfinder['paths']
elec_path_trimmed = elec_path[1:-1,1:-1]
pd.DataFrame(elec_path).to_csv("temp/dijkstra/elec_path_%s.csv" %(name))
distance_path = pathfinder['distance']
pd.DataFrame(distance_path).to_csv("temp/dijkstra/distance_path_%s.csv" %(name))
rendering_path = pathfinder['rendering']
pd.DataFrame(rendering_path).to_csv("temp/dijkstra/rendering_path_%s.csv" %(name))
print("Saving results to csv from Pathfinder")
#remove the "grid" path from the pathfinder path
grid_csv = np.genfromtxt(os.path.join('temp/dijkstra', "grid_weight.csv"), delimiter=',')
removed_grid = removing_grid(elec_path, grid_csv)
np.savetxt(os.path.join('temp/dijkstra', "path_without_grid.csv"), removed_grid, delimiter=',')
# print the algortihm to raster
print("Converting results from Pathfinder to raster")
raster_pathfinder = make_raster(elec_path_trimmed, name)

files = os.listdir(proj_path)
shapefiles = []
for file in files:
    if file.endswith('.shp'):
        f = os.path.join('temp/', file)
        shapefiles += [f]
for f in shapefiles:
    name, end = os.path.splitext(os.path.basename(f))
    pathmask = masking(f, raster_pathfinder, '%s_Kenya_pathfinder.tif' %(name))
    weightmask = masking(f, weights_raster, '%s_weight.tif' % (name))

print("Calculating Pathfinder for each cell")
#This is the final version and the other is as reference for unceratinty analysis
for f in shapefiles:
    name, end = os.path.splitext(os.path.basename(f))
    weight_raster_cell = masking(f, weights_raster, '%s_weight.tif' %(name))
    elec_raster_cell = masking(f, elec_raster, '%s_elec.tif' % (name))

    # make csv files for Dijkstra
    weight_csv = make_weight_numpyarray(weight_raster_cell, name)
    target_csv = make_target_numpyarray(elec_raster_cell, name)
    print(name)
    if os.path.isfile(target_csv) is False:
        continue
    else:
        targets = np.genfromtxt(os.path.join('temp/dijkstra', "%s_target.csv" % (name)), delimiter=',')
        weights = np.genfromtxt(os.path.join('temp/dijkstra', "%s_weight.csv" % (name)), delimiter=',')
        origin_csv = make_origin_numpyarray(target_csv, name)
        origin = np.genfromtxt(os.path.join('temp/dijkstra', "%s_origin.csv" % (name)), delimiter=',')
        # Run the Pathfinder alogrithm seek(origins, target, weights, path_handling='link', debug=False, film=False)
        print("Calculating Pathfinder")
        pathfinder = seek(origin, targets, weights, path_handling='link', debug=False, film=False)
        elec_path = pathfinder['paths']
        elec_path_trimmed = elec_path[1:-1,1:-1]
        pd.DataFrame(elec_path).to_csv("temp/dijkstra/elec_path_%s.csv" % (name))
        distance_path = pathfinder['distance']
        pd.DataFrame(distance_path).to_csv("temp/dijkstra/distance_path_%s.csv" % (name))
        rendering_path = pathfinder['rendering']
        pd.DataFrame(rendering_path).to_csv("temp/dijkstra/rendering_path_%s.csv" % (name))
        print("Saving results to csv from Pathfinder")
        print("Converting results from Pathfinder to raster")
        raster_pathfinder = make_raster(elec_path_trimmed, name)