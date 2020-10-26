import geopandas as gpd
from shapely.geometry import Point, Polygon, LineString, mapping, MultiLineString, MultiPoint
import fiona
fiona.supported_drivers
from osgeo import gdal

import os
import numpy as np
from GIS_functions import *
import ipywidgets as widgets
from IPython.display import display
from rasterstats import zonal_stats
import rasterio
import rasterio.fill
from rasterio.mask import mask
from rasterio.merge import merge
import pycrs
from rasterio.plot import show
from fiona.crs import from_epsg
import json
#from earthpy import clip
#import earthpy.spatial as es
import tkinter as tk
from tkinter import filedialog, messagebox
import datetime
import warnings
import scipy.spatial
warnings.filterwarnings('ignore')

#projected coordinate system for the analysis: WGS84 UMT 37S
crs = 'EPSG:32737'
wgs84 = 'EPSG: 4326'
#outbox folder
workspace = r'C:\Users\nandi\Box Sync\PhD\Paper 3-OSeMOSYS 40x40\Snakemake\GIS_data'

#import files admin and population
adm_path = r'C:\Users\nandi\Box Sync\PhD\Paper 3-OSeMOSYS 40x40\Snakemake\datasets\gadm36_KEN_shp\gadm36_KEN_0.shp'
admin = gpd.read_file(adm_path)

#POP mask with adm boundaries
pop_path = r'C:\Users\nandi\Box Sync\PhD\Paper 3-OSeMOSYS 40x40\Snakemake\datasets\ken_ppp_2015_UNadj.tif'
pop_out_tif = r'C:\Users\nandi\Box Sync\PhD\Paper 3-OSeMOSYS 40x40\Snakemake\datasets\pop_mask.tif'
pop_filename = r'C:\Users\nandi\Box Sync\PhD\Paper 3-OSeMOSYS 40x40\Snakemake\datasets\pop_mask'
viirs1_path = r'C:\Users\nandi\Box Sync\PhD\Paper 3-OSeMOSYS 40x40\Snakemake\datasets\SVDNB_npp_20190401-20190430_00N060W_vcmslcfg_v10_c201905191000\SVDNB_npp_20190401-20190430_00N060W_vcmslcfg_v10_c201905191000.avg_rade9h.tif'
viirs2_path = r'C:\Users\nandi\Box Sync\PhD\Paper 3-OSeMOSYS 40x40\Snakemake\datasets\SVDNB_npp_20190401-20190430_75N060W_vcmslcfg_v10_c201905191000\SVDNB_npp_20190401-20190430_75N060W_vcmslcfg_v10_c201905191000.avg_rade9h.tif'
viirs = r'C:\Users\nandi\Box Sync\PhD\Paper 3-OSeMOSYS 40x40\Snakemake\datasets\viirs-mosaic.tif'
viirs_out = r'C:\Users\nandi\Box Sync\PhD\Paper 3-OSeMOSYS 40x40\Snakemake\datasets\viirs-mosaic_masked.tif'

print("Mosaic raster")
mosaic_raster(viirs1_path, viirs2_path, viirs)
print("mask raster")
mask_raster(pop_path, pop_out_tif, admin) #mask raster (path to raster, out tif file, admin shape file)
mask_raster(viirs, viirs_out, admin) #mask raster (path to raster, out tif file, admin shape file)
print("raster to point")
raster_to_numpyarray(pop_out_tif)




#geopandas endproduct with pop, nightimelights, roads, transmissionlines,
settlements_in = [1,1]

#geopandas from raster
clipped_pop = [1,1]
