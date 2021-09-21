# Runs all the GIS-steps for Pathfinder
#
# Author: Nandi Moksnes
# Date: 17 September 2021
# Python version: 3.8


import os
import sys
import geopandas as gpd
from shapely.geometry import Point, Polygon, LineString, mapping, MultiLineString, MultiPoint
from fiona import supported_drivers
from fiona.crs import from_epsg
import gdal
from osgeo import gdal_array
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
import numpy as np
import fiona
import rasterio
import rasterio.mask
import ogr
import struct
import pandas as pd
import subprocess
subprocess.call('gdal_translate -of GTiff -ot Int16 input.tif output.tif')
from rasterio.merge import merge
from osgeo import gdal, ogr, gdalconst
gdal.UseExceptions()
from shapely.geometry import MultiLineString

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def convert_zero_to_one(file, cut_off):
    gpdf = gpd.read_file(file)

    gpdf.loc[(gpdf.elec == 1) | ((gpdf.elec ==0) & (gpdf.grid_code < cut_off)),'dijkstra'] = 0
    gpdf.loc[((gpdf.elec == 0) & (gpdf.grid_code >= cut_off)),'dijkstra'] = 1

    gpdf.to_file('../Projected_files/zero_to_one_elec.shp')
    return ('../Projected_files/zero_to_one_elec.shp')

def rasterize_elec(file, proj_path):
    # Rasterizing the point file
    InputVector = file
    _, filename = os.path.split(file)
    name, ending = os.path.splitext(filename)

    OutputImage = os.path.join(proj_path, name + '.tif')

    RefImage = os.path.join('../Projected_files', 'masked_UMT37S_ken_ppp_2018_1km_Aggregated.tif')

    gdalformat = 'GTiff'
    datatype = gdal.GDT_Int32
    #burnVal = 1  # value for the output image pixels
    # Get projection info from reference image
    Image = gdal.Open(RefImage, gdal.GA_ReadOnly)

    # Open Shapefile
    Shapefile = ogr.Open(InputVector)
    Shapefile_layer = Shapefile.GetLayer()

    # Rasterise
    Output = gdal.GetDriverByName(gdalformat).Create(OutputImage, Image.RasterXSize, Image.RasterYSize, 1, datatype,
                                                     options=['COMPRESS=DEFLATE'])
    Output.SetProjection(Image.GetProjectionRef())
    Output.SetGeoTransform(Image.GetGeoTransform())

    # Write data to band 1
    Band = Output.GetRasterBand(1)
    Band.SetNoDataValue(0)
    gdal.RasterizeLayer(Output, [1], Shapefile_layer, options = ["ATTRIBUTE=dijkstra"])

    # Build image overviews
    subprocess.call("gdaladdo --config COMPRESS_OVERVIEW DEFLATE " + OutputImage + " 2 4 8 16 32 64", shell=True)
    # Close datasets
    Band = None
    Output = None
    Image = None

    return (OutputImage)

def merge_road_grid(proj_path):
    """This function concatinates the shapefiles which contains the keyword '33kV' and '66kV'

    :param proj_path:
    :return:
    """
    current = os.getcwd()
    os.chdir(proj_path)
    files = os.listdir(proj_path)
    shapefiles = []
    for file in files:
        if file.endswith('.shp'):
            f = os.path.abspath(file)
            shapefiles += [f]
    keyword = ['Concat_MV_lines_UMT37S', 'Concat_Transmission_lines_UMT37S', 'UMT37S_Roads', '11kV']
    dijkstraweight = []
    out = [f for f in shapefiles if any(xs in f for xs in keyword)]
    for f in out:
        shpfile = gpd.read_file(f)
        dijkstraweight += [shpfile]

    gdf = pd.concat([shp for shp in dijkstraweight], sort=False).pipe(gpd.GeoDataFrame)
    gdf.to_file("../Projected_files/dijkstraweight.shp")
    os.chdir(current)
    return("../Projected_files/dijkstraweight.shp")

def highway_weights(path_highw, path):
    path_highway = os.path.join(path,'highways_weights.shp')
    highways = gpd.read_file(path_highw)
    #Length_m_ represents all lines that are grid and Length_km represents road
    keep = ['Length_km', 'Length_m_']
    highways_col = highways[keep]
    pd.options.mode.chained_assignment = None
    highways_col['weight'] = 1
    highways_col = highways_col.astype('float64')
    highways_col.loc[highways_col['Length_km']>0, ['weight']] = 1/2
    highways_col.loc[highways_col['Length_m_']>0, ['weight']] = 0

    schema = highways.geometry  #the geometry same as highways
    gdf = gpd.GeoDataFrame(highways_col, crs=32737, geometry=schema)
    gdf.to_file(driver = 'ESRI Shapefile', filename= path_highway)

    return (path_highway)

# Pathfinder results to raster
def make_raster(pathfinder, s):
    path = os.path.join('../Projected_files','%s_e.tif' %(s))
    zoom_20 = gdal.Open(path)
    dst_filename = os.path.join('temp/dijkstra','path_%s.tif' %(s))
    geo_trans = zoom_20.GetGeoTransform()
    pixel_width = 924
    x_min = geo_trans[0]    #x-top left corner in raster
    y_max = geo_trans[3]    #y-top left corner in raster
    x_max = x_min + geo_trans[1] * zoom_20.RasterXSize
    y_min = y_max + geo_trans[5] * zoom_20.RasterYSize
    x_res = zoom_20.RasterXSize
    y_res = zoom_20.RasterYSize
    driver = gdal.GetDriverByName('GTiff')
    dataset = driver.Create(dst_filename,x_res, y_res, 1,gdal.GDT_Float32)
    dataset.GetRasterBand(1).WriteArray(pathfinder)

    proj=zoom_20.GetProjection()
    dataset.SetGeoTransform(geo_trans)
    dataset.SetProjection(proj)
    dataset.FlushCache()
    dataset=None
    east_ntl = None
    return None

def shape_to_raster(path, path_highway, country):
    output = os.path.join(sys.path[0],'%s_highways_weights.tif' %(country))
    pixel_width = 38    #Zoom level 20 38mx38m
    data = gdal.Open(path)
    geo_transform = data.GetGeoTransform()
    x_min = geo_transform[0]    #x-top left corner in raster
    y_max = geo_transform[3]    #y-top left corner in raster
    x_max = x_min + geo_transform[1] * data.RasterXSize
    y_min = y_max + geo_transform[5] * data.RasterYSize
    x_res = round(data.RasterXSize*(geo_transform[1]/pixel_width))
    y_res = round(data.RasterYSize*(geo_transform[1]/pixel_width))
    mb_v = ogr.Open(path_highway)
    mb_l = mb_v.GetLayer()
    target_ds = gdal.GetDriverByName('GTiff')
    ds = target_ds.Create(output, x_res, y_res, 1,  gdal.GDT_Float32)
    ds.SetGeoTransform([x_min, pixel_width, 0, y_max, 0, -pixel_width])
    band = ds.GetRasterBand(1)
    NoData_value = 1
    proj = data.GetProjection()
    ds.SetProjection(proj)
    band.SetNoDataValue(NoData_value)
    band.FlushCache()
    gdal.RasterizeLayer(ds, [1], mb_l, options = ["ATTRIBUTE=weight"])

    weights = ds.ReadAsArray()

    ds = None
    data = None
    mb_v = None

    return weights


def make_weight_numpyarray(file, s):
    raster = gdal.Open(file)
    weight = raster.ReadAsArray()
    NoValue = weight < -3.4*10**38  #related to GDAL which sets NoValue to -3.4e+38
    weight[NoValue] = 1

    if np.count_nonzero(weight) != 0:
        np.savetxt(os.path.join('temp/dijkstra', "%s_weight.csv" %(s)), weight, delimiter=',')
    raster = None # close the raster

    return None

def make_origin_numpyarray(file, s):
    nparray = np.genfromtxt((file), delimiter=',')
    row = int(round(nparray.shape[0]/2))
    col = int(round(nparray.shape[1]/2))
    origins = np.zeros(nparray.shape)

    if nparray[row, col] == 0:
        origins[row,col] = 1
    else:
        row = row +1
        col = col +1
        origins[row,col] = 1

    if np.count_nonzero(origins) != 0:
        np.savetxt(os.path.join('temp/dijkstra', "%s_origin.csv" %(s)), origins, delimiter=',')
    return None

def make_target_numpyarray(file, s):
    raster = gdal.Open(file)
    target = raster.ReadAsArray()
    NoValue = target > 2
    target[NoValue] = 0

    if np.count_nonzero(target) != 0:
        np.savetxt(os.path.join('temp/dijkstra', "%s_target.csv" %(s)), target, delimiter=',')
    raster = None # close the raster

    return os.path.join('temp/dijkstra', "%s_target.csv" %(s))

def rasterize_road(file, proj_path):
    # Rasterizing the point file
    InputVector = file
    #_, filename = os.path.split(file)
    #name, ending = os.path.splitext(filename)
    OutputImage = os.path.join(proj_path, 'weights.tif')
    RefImage = os.path.join('../Projected_files', 'masked_UMT37S_ken_ppp_2018_1km_Aggregated.tif')

    gdalformat = 'GTiff'
    datatype = gdal.GDT_Float32
    burnVal = 1  # value for the output image pixels
    # Get projection info from reference image
    Image = gdal.Open(RefImage, gdal.GA_ReadOnly)

    # Open Shapefile
    Shapefile = ogr.Open(InputVector)
    Shapefile_layer = Shapefile.GetLayer()

    # Rasterise
    Output = gdal.GetDriverByName(gdalformat).Create(OutputImage, Image.RasterXSize, Image.RasterYSize, 1, datatype ) #options=['COMPRESS=DEFLATE']
    Output.SetProjection(Image.GetProjectionRef())
    Output.SetGeoTransform(Image.GetGeoTransform())

    # Write data to band 1
    band = Output.GetRasterBand(1)
    band.SetNoDataValue(1)
    gdal.RasterizeLayer(Output, [1], Shapefile_layer, options = ["ATTRIBUTE=weight"])

    # Build image overviews
    subprocess.call("gdaladdo --config COMPRESS_OVERVIEW DEFLATE " + OutputImage + " 2 4 8 16 32 64", shell=True)
    # Close datasets
    band = None
    Output = None
    Image = None
    # Shapefile = None

    return OutputImage

def masking(shape,tif_file, s):
    """ This function masks the raster data (tif-file) with the GADM Admin 0 boundaries (admin)
    :param bounds:
    :param tif_file:
    :return: tif_file
    """

    with fiona.open(shape, "r") as shapefile:
        shapes = [feature["geometry"] for feature in shapefile]
    with rasterio.open(tif_file) as src:
        out_image, out_transform = rasterio.mask.mask(src, shapes, crop=True)
        out_meta = src.meta
    out_meta.update({"driver": "GTiff",
                     "height": out_image.shape[1],
                     "width": out_image.shape[2],
                     "transform": out_transform})

    with rasterio.open('../Projected_files/%s' %(s), "w", **out_meta) as dest:
        dest.write(out_image)
    return('../Projected_files/%s' %(s))
