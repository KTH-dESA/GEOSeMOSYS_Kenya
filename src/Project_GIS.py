import geopandas as gpd
import os
import fiona
import rasterio
rasterio.gdal_version()
import rasterio.fill
from rasterio.mask import mask
import tkinter as tk
import gdal
import warnings
warnings.filterwarnings('ignore')
from osgeo import ogr, osr, gdal
from os import listdir
from os.path import isfile, join, isdir
import sys
import shutil
gdal.UseExceptions()

root = tk.Tk()
root.withdraw()
root.attributes("-topmost", True)

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

def project_raster(rasterdata, output_raster):
    gdal.Warp(output_raster, rasterdata, dstSRS='EPSG:32737')
    return()

def project_vector(vectordata, outputvector):

    gdf = gpd.read_file(vectordata)
    gdf_umt37 = gdf.to_crs("epsg:32737")
    gdf_umt37.to_file(outputvector)

    return()

def main(GIS_files_path):
    """
    Reads the GIS-layers and separates them by raster and vector data

    """
    basedir = os.getcwd()
    os.chdir(GIS_files_path)
    current = os.getcwd()
    dirpath = [d for d in listdir(current) if isdir(join(current, d))]
    onlydir = [os.path.join(current, d, '') for d in dirpath]
    dirpaths = onlydir + [str(current+'/')]
    for i in dirpaths:
        filepaths = [f for f in listdir(i) if isfile(join(i,f))]
        onlyfiles = [os.path.join(current,f) for f in filepaths]
        for files in onlyfiles:
            _, filename = os.path.split(files)
            name, ending = os.path.splitext(filename)
            if ending == '.shp':
                project_vector(files, os.path.join(i,"UMT37S_%s" % (filename)))
                for f in onlyfiles:
                    _, file = os.path.split(f)
                    shutil.copy(os.path.join(i, file), os.path.join(current, '..\Projected_files'))
            elif ending == '.tif':
                masking(os.path.join(i,'gadm36_KEN_shp\gadm36_KEN_0.shp'), os.path.join(i,'\%s_masked.tif' % (name)))
                project_raster(os.path.join(i,'\%s_masked.tif' % (name)), os.path.join(i,"%smasked_UMT37S.tif" % (name)))
            else:
                pass
        os.chdir(i)
        dirpath2 = [d for d in listdir(i) if isdir(join(i, d))]
        dirpaths2 = [os.path.join(i, d, '') for d in dirpath2]
        for j in dirpaths2:
            filepaths2 = [f for f in listdir(j) if isfile(join(j,f))]
            onlyfiles2 = [os.path.join(j,f) for f in filepaths2]
            for files2 in onlyfiles2:
                _, filename2 = os.path.split(files2)
                name2, ending2 = os.path.splitext(filename2)
                if ending2 == '.shp':
                    project_vector(files2, os.path.join(j,"UMT37S_%s" % (filename2)))
                    for f in onlyfiles2:
                        _, file = os.path.split(f)
                        shutil.copy(os.path.join(j,file), os.path.join(current, '..\Projected_files'))
                elif ending2 == '.tif':
                    masking(os.path.join(j,'gadm36_KEN_shp\gadm36_KEN_0.shp'), os.path.join(j,'%s_masked.tif' % (name2)))
                    project_raster(os.path.join(j,'\%s_masked.tif' % (name2)), os.path.join(j,"%smasked_UMT37S.tif" % (name2)))
                else:
                    pass
        os.chdir(current)
    return ()

if __name__ == "__main__":
    GIS_files_path = sys.argv[1]
    main(GIS_files_path)
