# Runs all the GIS-steps for Pathfinder
#
# Author: Nandi Moksnes

# Date: 17 September 2021
# Python version: 3.8


import os
import geopandas as gpd
import gdal
import matplotlib
matplotlib.use('Agg')
import numpy as np
import fiona
import rasterio
import rasterio.mask
import ogr
import pandas as pd
import subprocess
subprocess.call('gdal_translate -of GTiff -ot Int16')
#from rasterio.merge import merge
from osgeo import gdal, ogr, gdalconst
gdal.UseExceptions()
#from shapely.geometry import MultiLineString

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
    Shapefile= None
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
    keyword = ['Concat_MV_lines_UMT37S', 'Concat_Transmission_lines_UMT37S','11kV', 'UMT37S_Roads']
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
    highways_col.loc[highways_col['Length_m_']>0, ['weight']] = 0.01

    schema = highways.geometry  #the geometry same as highways
    gdf = gpd.GeoDataFrame(highways_col, crs=32737, geometry=schema)
    gdf.to_file(driver = 'ESRI Shapefile', filename= path_highway)

    return (path_highway)

# Pathfinder results to raster
def make_raster(pathfinder, s):
    dst_filename = os.path.join('temp/dijkstra','path_%s.tif' %(s))
    path = os.path.join('../Projected_files','zero_to_one_elec.tif')
    zoom_20 = gdal.Open(path)
    geo_trans = zoom_20.GetGeoTransform()
    pixel_width = 924

    # You need to get those values like you did.
    x_pixels = zoom_20.RasterXSize  # number of pixels in x
    y_pixels = zoom_20.RasterYSize # number of pixels in y
    PIXEL_SIZE = 924  # size of the pixel...
    x_min = geo_trans[0]
    y_max = geo_trans[3]
    wkt_projection = zoom_20.GetProjection()

    driver = gdal.GetDriverByName('GTiff')
    dataset = driver.Create(
        dst_filename,
        x_pixels,
        y_pixels,
        1,
        gdal.GDT_Float32, )

    dataset.SetGeoTransform((
        x_min, PIXEL_SIZE,
        0,
        y_max,
        0,
        -PIXEL_SIZE))

    dataset.SetProjection(wkt_projection)
    dataset.GetRasterBand(1).WriteArray(pathfinder)
    dataset.FlushCache()  # Write to disk.
    return

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
        origin_found = False
        maxrow = nparray.shape[0] - row
        j = row
        for i in (range(1, maxrow)):
            j = j +1
            col = col
            if nparray[j, col] == 0:
                origins[j,col] = 1
                origin_found = True
                break
        k = col
        for i in (range(1, maxrow)):
            if origin_found == True:
                break
            row = row
            k = k +1
            if nparray[row, k] == 0:
                origins[row,k] = 1
                origin_found = True
                break

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
    Image2 = gdal.Open(RefImage, gdal.GA_ReadOnly)

    # Open Shapefile
    Shapefile = ogr.Open(InputVector)
    Shapefile_layer = Shapefile.GetLayer()

    # Rasterise
    Output2 = gdal.GetDriverByName(gdalformat).Create(OutputImage, Image2.RasterXSize, Image2.RasterYSize, 1, datatype, options=['COMPRESS=DEFLATE'] ) #
    Output2.SetProjection(Image2.GetProjectionRef())
    Output2.SetGeoTransform(Image2.GetGeoTransform())

    # Write data to band 1
    band2 = Output2.GetRasterBand(1)
    band2.SetNoDataValue(1)
    gdal.RasterizeLayer(Output2, [1], Shapefile_layer, options = ["ATTRIBUTE=weight"])

    # Build image overviews
    subprocess.call("gdaladdo --config COMPRESS_OVERVIEW DEFLATE " + OutputImage + " 2 4 8 16 32 64", shell=True)
    # Close datasets
    band2 = None
    Output2 = None
    Image2 = None
    Shapefile = None

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
