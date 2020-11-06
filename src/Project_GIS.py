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
from osgeo import gdal
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
    Reads the GIS-layers and separates them by raster and vector data.
    Projects the data to WGS84 UMT37S
    Moves all files to ../Pjected_files

    """
    basedir = os.getcwd()
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
    allFiles = [os.path.join(dp, f) for dp, dn, filenames in os.walk(current) for f in filenames]
    keyword = 'UMT37S'
    for fname in allFiles:
        if keyword in fname:
            shutil.copy(fname, os.path.join(current, '..\Projected_files'))

    return ()

if __name__ == "__main__":
    GIS_files_path = sys.argv[1]
    main(GIS_files_path)