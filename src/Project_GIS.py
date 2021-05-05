# Author: KTH dESA Last modified by Nandi Moksnes
# Date: 2021-04
# Python version: 3.8
import geopandas as gpd
import rioxarray
import xarray
from shapely.geometry import mapping
import pandas as pd
import os
import fiona
import rasterio
rasterio.gdal_version()
import rasterio.fill
from rasterio.mask import mask
import gdal
import warnings
warnings.filterwarnings('ignore')
from osgeo import gdal
import sys
import shutil
gdal.UseExceptions()


def masking(admin,tif_file):

    with fiona.open(admin, "r") as shapefile:
        shapes = [feature["geometry"] for feature in shapefile]
    with rasterio.open(tif_file) as src:
        out_image, out_transform = rasterio.mask.mask(src, shapes, crop=True)
        out_meta = src.meta
    out_meta.update({"driver": "GTiff",
                     "height": out_image.shape[1],
                     "width": out_image.shape[2],
                     "transform": out_transform})

    with rasterio.open(tif_file, "w", **out_meta) as dest:
        dest.write(out_image)

    return(tif_file)

def project_raster(rasterdata, output_raster):
    print(rasterdata)
    input_raster = gdal.Open(rasterdata)
    gdal.Warp(output_raster, input_raster, dstSRS="EPSG:32737")
    return()

def project_vector(vectordata, outputvector):
    print(vectordata)
    gdf = gpd.read_file(vectordata)
    gdf_umt37 = gdf.to_crs({'init':'epsg:32737'})
    gdf_umt37.to_file(outputvector)

    return()

def merge_transmission(proj_path):
    current = os.getcwd()
    os.chdir(proj_path)
    files = os.listdir(proj_path)
    shapefiles = []
    for file in files:
        if file.endswith('.shp'):
            f = os.path.abspath(file)
            shapefiles += [f]
    keyword = 'kV'
    tmiss_list = []
    for fname in shapefiles:
        if keyword in fname:
            shpfile = gpd.read_file(fname)
            tmiss_list += [shpfile]

    gdf = pd.concat([shp for shp in tmiss_list]).pipe(gpd.GeoDataFrame)
    gdf.to_file("../Projected_files/Concat_Transmission_lines_UMT37S.shp")
    os.chdir(current)

def merge_minigrid(proj_path):
    current = os.getcwd()
    os.chdir(proj_path)
    files = os.listdir(proj_path)
    shapefiles = []
    for file in files:
        if file.endswith('.shp'):
            f = os.path.abspath(file)
            shapefiles += [f]
    keyword = 'MiniGrid'
    minigr_list = []
    for fname in shapefiles:
        if keyword in fname:
            shpfile = gpd.read_file(fname)
            minigr_list += [shpfile]

    gdf = pd.concat([shp for shp in minigr_list]).pipe(gpd.GeoDataFrame)
    gdf.set_crs(epsg=32737, inplace=True)
    gdf.to_file("../Projected_files/Concat_Mini-grid_UMT37S.shp")
    os.chdir(current)

def main(GIS_files_path):
    """
    Reads the GIS-layers and separates them by raster and vector data.
    Projects the data to WGS84 UMT37S
    Moves all files to ../Projected_files
    Merges the files named 'kV' to one merged shape file
    Merges the files named 'MiniGrid' to one merged shape file

    """
    try:
       #  basedir = os.getcwd()
        os.chdir(GIS_files_path)
        current = os.getcwd()
        #All shp-files in all folders in dir current
        shpFiles = [os.path.join(dp, f) for dp, dn, filenames in os.walk(current) for f in filenames if
                  os.path.splitext(f)[1] == '.shp']
        for s in shpFiles:
            path, filename = os.path.split(s)
            project_vector(s, os.path.join(path, "UMT37S_%s" % (filename)))
        #All tif-files in all folders in dir current
        tifFiles = [os.path.join(dp, f) for dp, dn, filenames in os.walk(current) for f in filenames if
                  os.path.splitext(f)[1] == '.tif']
        for t in tifFiles:
            path, filename = os.path.split(t)
            masking(os.path.join(current,'gadm36_KEN_shp\gadm36_KEN_0.shp'), t)
            project_raster(os.path.join(path,'%s' % (filename)), os.path.join(path,"masked_UMT37S_%s" % (filename)))

        #All files containing "UMT37S" is copied to ../Projected_files dir
        def create_dir(dir):
            if not os.path.exists(dir):
                os.makedirs(dir)
        create_dir(('../Projected_files'))
        allFiles = [os.path.join(dp, f) for dp, dn, filenames in os.walk(current) for f in filenames]
        keyword = 'UMT37S'
        for fname in allFiles:
            if keyword in fname:
                shutil.copy(fname, os.path.join(current, '..\Projected_files'))
    except:
        os.chdir(basedir)
    os.chdir(basedir)
    merge_transmission('..\Projected_files')
    merge_minigrid('..\Projected_files')
    return ()

if __name__ == "__main__":
    basedir = os.getcwd()
    GIS_files_path = sys.argv[1]
    main(GIS_files_path)
    os.chdir(basedir)

