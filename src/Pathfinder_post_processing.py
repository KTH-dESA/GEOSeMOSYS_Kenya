from Pathfinder_GIS_steps import *
import numpy as np
import pandas as pd

projeted_fpath = '../Projected_files/'
tif_path = 'temp/dijkstra'
temp_path = 'temp'

current = os.getcwd()
os.chdir(tif_path)
files = os.listdir(tif_path)
tiffiles = []
for file in files:
    if file.endswith('.tif'):
        f = os.path.abspath(file)
        tiffiles += [f]
keyword = ['path']
dijkstraweight = []
out = [f for f in tiffiles if any(xs in f for xs in keyword)]
for f in out:
    rasterArray = f.ReadAsArray()
    dijkstraweight += [rasterArray]

os.chdir(current)

#clip the weights to retreieve the gridweights
weights_raster = "../Projected_files/weights.tif"
files = os.listdir(temp_path)
shapefiles = []
for file in files:
    if file.endswith('.shp'):
        f = os.path.join('temp/', file)
        shapefiles += [f]
for f in shapefiles:
    name, end = os.path.splitext(os.path.basename(f))
    weightmask = masking(f, weights_raster, '%s_weight.tif' % (name))
    weight_array = weightmask.ReadAsArray()

    remove_grid = 

#remove the "grid" path from the pathfinder path
grid_csv = np.genfromtxt(os.path.join('temp/dijkstra', "grid_weight.csv"), delimiter=',')
removed_grid = removing_grid(elec_path, grid_csv)
np.savetxt(os.path.join('temp/dijkstra', "path_without_grid.csv"), removed_grid, delimiter=',')
