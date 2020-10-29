import geopandas as gpd
import os
import fiona
import ipywidgets as widgets
from IPython.display import display
from rasterstats import zonal_stats
import rasterio
rasterio.gdal_version()
import rasterio.fill
from shapely.geometry import shape, mapping
import json
from earthpy import clip
import rasterstats as rs
import earthpy as et
import earthpy.plot as ep
from rasterio.mask import mask
from rasterio.merge import merge
import pycrs
import earthpy.spatial as es
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
import gdal
import sys
import datetime
import warnings
import pandas as pd
import scipy.spatial
warnings.filterwarnings('ignore')
from osgeo import ogr, osr, gdal
from os import listdir
from os.path import isfile, join
gdal.UseExceptions()

root = tk.Tk()
root.withdraw()
root.attributes("-topmost", True)

def project_raster(rasterdata, output_raster):
    gdal.Warp(output_raster, rasterdata, dstSRS='EPSG:32737')
    return()

def project_vector(vectordata, outputvector):

    driver = ogr.GetDriverByName('ESRI Shapefile')
    dataset = driver.Open(vectordata)
    layer = dataset.GetLayer()
    spatialref = layer.GetSpatialRef()

    targetspatialRef = osr.SpatialReference()
    targetspatialRef.ImportFromEPSG(32737)

    # set spatial reference and transformation
    transform = osr.CoordinateTransformation(spatialref, targetspatialRef)

    to_fill = ogr.GetDriverByName("Esri Shapefile")
    ds = to_fill.CreateDataSource(outputvector)
    outlayer = ds.CreateLayer('', targetspatialRef, ogr.wkbPolygon)
    outlayer.CreateField(ogr.FieldDefn('id', ogr.OFTInteger))

    # apply transformation
    i = 0

    for feature in layer:
        transformed = feature.GetGeometryRef()
        transformed.Transform(transform)

        geom = ogr.CreateGeometryFromWkb(transformed.ExportToWkb())
        defn = outlayer.GetLayerDefn()
        feat = ogr.Feature(defn)
        feat.SetField('id', i)
        feat.SetGeometry(geom)
        outlayer.CreateFeature(feat)
        i += 1
        feat = None

    ds = None
    return()

def main(GIS_files_path):
    """
    Reads the GIS-layers and separates them by raster and vector data

    """
    filepaths = [f for f in listdir(GIS_files_path) if isfile(join(GIS_files_path, f))]
    onlyfiles = [os.path.join(GIS_files_path, f) for f in filepaths]
    for files in onlyfiles:
        _, filename = os.path.split(files)
        name, ending = os.path.splitext(filename)
        if ending == '.shp':
            project_vector(files, GIS_files_path+name+"_UMT37S")
        elif ending == '.tif':
            project_raster(files, GIS_files_path+name+"_UMT37S")
        else:
            pass
    return ()

if __name__ == "__main__":
    GIS_files_path = r'C:\Users\nandi\Box Sync\PhD\Paper 3-OSeMOSYS 40x40\Snakemake\GEOSeMOSYS_reprod\GEOSeMOSYS_Kenya\GIS_data'
    main(GIS_files_path)






















def raster_to_numpyarray(pop_file): #make raster to point
    ds = gdal.Open(pop_file)
    pop_array = np.array(ds.GetRasterBand(1).ReadAsArray())
    print(np.size(pop_array))
    return pop_array

def mosaic_raster(path1, path2, out_fp):
    # mosaic viirs dataset
    src_files_to_mosaic = []
    src1 = rasterio.open(path1)
    src_files_to_mosaic.append(src1)
    src2 = rasterio.open(path2)
    src_files_to_mosaic.append(src2)

    mosaic, out_trans = merge(src_files_to_mosaic)
    out_meta = src1.meta.copy()
    print(out_meta)
    epsg_code = int(src1.crs.data['init'][5:])
    print(epsg_code)
    out_meta.update({"driver": "GTiff",
                     "height": mosaic.shape[1],
                     "width": mosaic.shape[2],
                     "transform": out_trans,
                     "crs": epsg_code
                     })
    with rasterio.open(out_fp, "w", **out_meta) as dest:
        dest.write(mosaic)

def mask_raster(path, out_tif, admin):
    kenya_pop = rasterio.open(path)

    def getFeatures(gdf):
        """Function to parse features from GeoDataFrame in such a manner that rasterio wants them"""
        import json
        return [json.loads(gdf.to_json())['features'][0]['geometry']]

    coords = getFeatures(admin)
    print(coords)
    out_img, out_transform = mask(kenya_pop, shapes=coords, crop=True)

    out_meta = kenya_pop.meta.copy()
    print(out_meta)

    epsg_code = int(kenya_pop.crs.data['init'][5:])
    print(epsg_code)

    out_meta.update({"driver": "GTiff",
                     "height": out_img.shape[1],
                     "width": out_img.shape[2],
                     "transform": out_transform,
                     "crs": pycrs.parse.from_epsg_code(epsg_code).to_proj4()})

    with rasterio.open(out_tif, "w", **out_meta) as dest:
        dest.write(out_img)


########################################################################################################################
def processing_raster(name, method, clusters):
    messagebox.showinfo('OnSSET', 'Select the ' + name + ' map')
    raster = rasterio.open(filedialog.askopenfilename(filetypes=(("rasters", "*.tif"), ("all files", "*.*"))))

    clusters = zonal_stats(
        clusters,
        raster.name,
        stats=[method],
        prefix=name, geojson_out=True, all_touched=True)

    print(datetime.datetime.now())
    return clusters


def processing_elevation_and_slope(name, method, clusters, workspace, crs):
    messagebox.showinfo('OnSSET', 'Select the ' + name + ' map')
    raster = rasterio.open(filedialog.askopenfilename(filetypes=(("rasters", "*.tif"), ("all files", "*.*"))))

    clusters = zonal_stats(
        clusters,
        raster.name,
        stats=[method],
        prefix=name, geojson_out=True, all_touched=True)

    gdal.Warp(workspace + r"\dem.tif", raster.name, dstSRS=crs)

    def calculate_slope(DEM):
        gdal.DEMProcessing(workspace + r'\slope.tif', DEM, 'slope')
        with rasterio.open(workspace + r'\slope.tif') as dataset:
            slope = dataset.read(1)
        return slope

    slope = calculate_slope(workspace + r"\dem.tif")

    slope = rasterio.open(workspace + r'\slope.tif')
    gdal.Warp(workspace + r'\slope_4326.tif', slope.name, dstSRS='EPSG:4326')
    slope_4326 = rasterio.open(workspace + r'\slope_4326.tif')

    clusters = zonal_stats(
        clusters,
        slope_4326.name,
        stats=["majority"],
        prefix="sl_", all_touched=True, geojson_out=True)

    print(datetime.datetime.now())
    return clusters


def finalizing_rasters(workspace, clusters, crs):
    output = workspace + r'\placeholder.geojson'
    with open(output, "w") as dst:
        collection = {
            "type": "FeatureCollection",
            "features": list(clusters)}
        dst.write(json.dumps(collection))

    clusters = gpd.read_file(output)
    os.remove(output)

    print(datetime.datetime.now())
    return clusters

def preparing_for_vectors(workspace, clusters, crs):
    clusters.crs = {'init' :'epsg:4326'}
    clusters = clusters.to_crs({ 'init': crs})
    points = clusters.copy()
    points["geometry"] = points["geometry"].centroid
    points.to_file(workspace + r'\clusters_cp.shp', driver='ESRI Shapefile')
    print(datetime.datetime.now())
    return clusters

def processing_lines(name, admin, crs, workspace, clusters):
    messagebox.showinfo('OnSSET', 'Select the ' + name + ' map')
    lines=gpd.read_file(filedialog.askopenfilename(filetypes = (("shapefile","*.shp"),("all files","*.*"))))

    lines_clip = clip.clip_shp(lines, admin)
    lines_clip.crs = {'init' :'epsg:4326'}
    lines_proj=lines_clip.to_crs({ 'init': crs})

    lines_proj.to_file(workspace + r"\ " + name + "_proj.shp", driver='ESRI Shapefile')

    line = fiona.open(workspace +  r"\ " + name + "_proj.shp")
    firstline = line.next()

    schema = {'geometry' : 'Point', 'properties' : {'id' : 'int'},}
    with fiona.open(workspace + r"\ " + name + "_proj_points.shp", "w", "ESRI Shapefile", schema) as output:
        for lines in line:
            if lines["geometry"] is not None:
                first = shape(lines['geometry'])
                length = first.length
                for distance in range(0,int(length),100):
                    point = first.interpolate(distance)
                    output.write({'geometry' :mapping(point), 'properties' : {'id':1}})

    lines_f = fiona.open(workspace + r"\ " + name + "_proj_points.shp")
    lines = gpd.read_file(workspace +  r"\ " + name + "_proj.shp")
    points = fiona.open(workspace + r'\clusters_cp.shp')

    geoms1 = [shape(feat["geometry"]) for feat in lines_f]
    s1 = [np.array((geom.xy[0][0], geom.xy[1][0])) for geom in geoms1]
    s1_arr = np.array(s1)

    geoms2 = [shape(feat["geometry"]) for feat in points]
    s2 = [np.array((geom.xy[0][0], geom.xy[1][0])) for geom in geoms2]
    s2_arr = np.array(s2)

    def do_kdtree(combined_x_y_arrays,points):
        mytree = scipy.spatial.cKDTree(combined_x_y_arrays)
        dist, indexes = mytree.query(points)
        return dist, indexes

    def vector_overlap(vec, settlementfile, column_name):
        vec.drop(vec.columns.difference(["geometry"]), 1, inplace=True)
        a = gpd.sjoin(settlementfile, vec, op = 'intersects')
        a[column_name + '2'] = 0
        return a

    results1, results2 = do_kdtree(s1_arr,s2_arr)

    z=results1.tolist()
    clusters[name+'Dist'] = z
    clusters[name+'Dist'] = clusters[name+'Dist']/1000

    a = vector_overlap(lines, clusters, name+'Dist')

    clusters = pd.merge(left = clusters, right = a[['id',name+'Dist2']], on='id', how = 'left')
    clusters.drop_duplicates(subset ="id", keep = "first", inplace = True)

    clusters.loc[clusters[name+'Dist2'] == 0, name+'Dist'] = 0

    del clusters[name+'Dist2']
    print(datetime.datetime.now())
    return clusters


def processing_points(name, admin, crs, workspace, clusters):
    messagebox.showinfo('OnSSET', 'Select the ' + name + ' map')
    points = gpd.read_file(filedialog.askopenfilename(filetypes=(("shapefile", "*.shp"), ("all files", "*.*"))))

    points_clip = clip.clip_shp(points, admin)
    points_clip.crs = {'init': 'epsg:4326'}
    points_proj = points_clip.to_crs({'init': crs})

    points_proj.to_file(workspace + r"\ " + name + "_proj.shp", driver='ESRI Shapefile')

    points_f = fiona.open(workspace + r"\ " + name + "_proj.shp")
    points = gpd.read_file(workspace + r"\ " + name + "_proj.shp")
    points2 = fiona.open(workspace + r'\clusters_cp.shp')

    geoms1 = [shape(feat["geometry"]) for feat in points_f]
    s1 = [np.array((geom.xy[0][0], geom.xy[1][0])) for geom in geoms1]
    s1_arr = np.array(s1)

    geoms2 = [shape(feat["geometry"]) for feat in points2]
    s2 = [np.array((geom.xy[0][0], geom.xy[1][0])) for geom in geoms2]
    s2_arr = np.array(s2)

    def do_kdtree(combined_x_y_arrays, points):
        mytree = scipy.spatial.cKDTree(combined_x_y_arrays)
        dist, indexes = mytree.query(points)
        return dist, indexes

    def vector_overlap(vec, settlementfile, column_name):
        vec.drop(vec.columns.difference(["geometry"]), 1, inplace=True)
        a = gpd.sjoin(settlementfile, vec, op='intersects')
        a[column_name + '2'] = 0
        return a

    results1, results2 = do_kdtree(s1_arr, s2_arr)

    z = results1.tolist()
    clusters[name + 'Dist'] = z
    clusters[name + 'Dist'] = clusters[name + 'Dist'] / 1000

    a = vector_overlap(points, clusters, name + 'Dist')

    clusters = pd.merge(left=clusters, right=a[['id', name + 'Dist2']], on='id', how='left')
    clusters.drop_duplicates(subset="id", keep="first", inplace=True)

    clusters.loc[clusters[name + 'Dist2'] == 0, name + 'Dist'] = 0

    del clusters[name + 'Dist2']
    print(datetime.datetime.now())
    return clusters


def processing_hydro(admin, crs, workspace, clusters, points, hydropowervalue,
                     hydropowerunit):
    points_clip = clip.clip_shp(points, admin)
    points_clip.crs = {'init': 'epsg:4326'}
    points_proj = points_clip.to_crs({'init': crs})

    points_proj.to_file(workspace + r"\HydropowerDist_proj.shp", driver='ESRI Shapefile')
    points_f = fiona.open(workspace + r"\HydropowerDist_proj.shp")
    points = gpd.read_file(workspace + r"\HydropowerDist_proj.shp")
    points2 = fiona.open(workspace + r'\clusters_cp.shp')

    geoms1 = [shape(feat["geometry"]) for feat in points_f]
    s1 = [np.array((geom.xy[0][0], geom.xy[1][0])) for geom in geoms1]
    s1_arr = np.array(s1)

    geoms2 = [shape(feat["geometry"]) for feat in points2]
    s2 = [np.array((geom.xy[0][0], geom.xy[1][0])) for geom in geoms2]
    s2_arr = np.array(s2)

    mytree = scipy.spatial.cKDTree(s1_arr)
    dist, indexes = mytree.query(s2_arr)

    def vector_overlap(vec, settlementfile, column_name):
        vec.drop(vec.columns.difference(["geometry"]), 1, inplace=True)
        a = gpd.sjoin(settlementfile, vec, op='intersects')
        a[column_name + '2'] = 0
        return a

    z1 = dist.tolist()
    z2 = indexes.tolist()
    clusters['HydropowerDist'] = z1
    clusters['HydropowerDist'] = clusters['HydropowerDist'] / 1000
    clusters['HydropowerFID'] = z2

    z3 = []
    for s in indexes:
        z3.append(points[hydropowervalue][s])

    clusters['Hydropower'] = z3

    x = hydropowerunit

    if x is 'MW':
        clusters['Hydropower'] = clusters['Hydropower'] * 1000
    elif x is 'kW':
        clusters['Hydropower'] = clusters['Hydropower']
    else:
        clusters['Hydropower'] = clusters['Hydropower'] / 1000

    a = vector_overlap(points, clusters, 'HydropowerDist')

    clusters = pd.merge(left=clusters, right=a[['id', 'HydropowerDist2']], on='id', how='left')
    clusters.drop_duplicates(subset="id", keep="first", inplace=True)

    clusters.loc[clusters['HydropowerDist2'] == 0, 'HydropowerDist'] = 0

    del clusters['HydropowerDist2']
    print(datetime.datetime.now())
    return clusters


def conditioning(clusters, workspace, popunit):
    clusters = clusters.to_crs({'init': 'epsg:4326'})

    clusters = clusters.rename(columns={"NightLight": "NightLights", popunit: "Pop", "GridCellAr": "GridCellArea"})

    if "landcovermajority" in clusters:
        clusters = clusters.rename(columns={"landcovermajority": "LandCover"})

    if "elevationmean" in clusters:
        clusters = clusters.rename(columns={"elevationmean": "Elevation"})

    if "sl_majority" in clusters:
        clusters = clusters.rename(columns={"sl_majority": "Slope"})

    if "ghimean" in clusters:
        clusters = clusters.rename(columns={"ghimean": "GHI"})

    if "traveltimemean" in clusters:
        clusters["traveltimemean"] = clusters["traveltimemean"] / 60
        clusters = clusters.rename(columns={"traveltimemean": "TravelHours"})
    elif "TravelHour" in clusters:
        clusters = clusters.rename(columns={"TravelHour": "TravelHours"})

    if "windmean" in clusters:
        clusters = clusters.rename(columns={"windmean": "WindVel"})

    if "Residentia" in clusters:
        clusters = clusters.rename(columns={"Resudentia": "ResidentialDemandTierCustom"})
    elif "customdemandmean" in clusters:
        clusters = clusters.rename(columns={"customdemandmean": "ResidentialDemandTierCustom"})
    else:
        clusters["ResidentialDemandTierCustom"] = 0

    if "Substation" in clusters:
        clusers = clusters.rename(columns={"Substation": "SubstationDist"})
    elif "SubstationDist" not in clusters:
        clusters["SubstationDist"] = 99

    if "CurrentHVL" in clusters:
        clusters = clusters.rename(columns={"CurrentHVL": "Existing_HVDist"})

    if "CurrentMVL" in clusters:
        clusters = clusters.rename(columns={"CurrentMVL": "Existing_MVDist"})

    if "PlannedHVL" in clusters:
        clusters = clusters.rename(columns={"PlannedHVL": "Planned_HVDist"})

    if "PlannedMVL" in clusters:
        clusters = clusters.rename(columns={"PlannedMVL": "Planned_MVDist"})

    if "Existing_HVDist" in clusters:
        clusters = clusters.rename(columns={"Existing_HVDist": "CurrentHVLineDist"})
        if "Planned_HVDist" in clusters:
            mask = (clusters['Planned_HVDist'] > clusters['CurrentHVLineDist'])
            clusters['Planned_HVDist'][mask] = clusters['CurrentHVLineDist']
            clusters = clusters.rename(columns={"Planned_HVDist": "PlannedHVLineDist"})
        else:
            clusters["PlannedHVLineDist"] = clusters["CurrentHVLineDist"]
    elif "Existing_HVDist" not in clusters and "Planned_HVDist" not in clusters:
        clusters["PlannedHVLineDist"] = 99
        clusters["CurrentHVLineDist"] = 0
    else:
        clusters["CurrentHVLineDist"] = 0
        clusters = clusters.rename(columns={"Planned_HVDist": "PlannedHVLineDist"})

    if "Existing_MVDist" in clusters:
        clusters = clusters.rename(columns={"Existing_MVDist": "CurrentMVLineDist"})
        if "Planned_MVDist" in clusters:
            mask = (clusters['Planned_MVDist'] > clusters['CurrentMVLineDist'])
            clusters['Planned_MVDist'][mask] = clusters['CurrentMVLineDist']
            clusters = clusters.rename(columns={"Planned_MVDist": "PlannedMVLineDist"})
        else:
            clusters["PlannedMVLineDist"] = clusters["CurrentMVLineDist"]
    elif "Existing_MVDist" not in clusters and "Planned_MVDist" not in clusters:
        clusters["PlannedMVLineDist"] = 99
        clusters["CurrentMVLineDist"] = 0
    else:
        clusters["CurrentMVLineDist"] = 0
        clusters = clusters.rename(columns={"Planned_MVDist": "PlannedMVLineDist"})

    if "RoadDist" not in clusters:
        clusters["RoadDist"] = 0

    if "Transforme" in clusters:
        clusters = clusters.rename(columns={"Transforme": "TransformerDist"})
    elif "TransformerDist" not in clusters:
        clusters["TransformerDist"] = 0

    if "Hydropower" not in clusters:
        clusters["Hydropower"] = 0

    if "Hydropow_1" in clusters:
        clusters = clusters.rename(columns={"Hydropow_1": "HydropowerDist"})
    elif 'HydropowerDist' not in clusters:
        clusters["HydropowerDist"] = 99

    if "Hydropow_2" in clusters:
        clusters = clusters.rename(columns={"Hydropow_2": "HydropowerFID"})
    elif "HydropowerFID" not in clusters:
        clusters["HydropowerFID"] = 0

    if "IsUrban" not in clusters:
        clusters["IsUrban"] = 0

    if "PerCapitaD" not in clusters:
        clusters["PerCapitaDemand"] = 0
    else:
        clusters = clusters.rename(columns={"PerCapitaD": "PerCapitaDemand"})

    if "HealthDema" not in clusters:
        clusters["HealthDemand"] = 0
    else:
        clusters = clusters.rename(columns={"HealthDema": "HealthDemand"})

    if "EducationD" not in clusters:
        clusters["EducationDemand"] = 0
    else:
        clusters = clusters.rename(columns={"EducationD": "EducationDemand"})

    if "AgriDemand" not in clusters:
        clusters["AgriDemand"] = 0

    if "Commercial" not in clusters:
        clusters["CommercialDemand"] = 0
    else:
        clusters = clusters.rename(columns={"Commercial": "CommercialDemand"})

    if "Conflict" not in clusters:
        clusters["Conflict"] = 0

    if "Electrific" not in clusters:
        clusters["ElectrificationOrder"] = 0
    else:
        clusters = clusters.rename(columns={"Electrific": "ElectrificationOrder"})

    if "Resident_1" not in clusters:
        clusters["ResidentialDemandTier1"] = 7.74
    else:
        clusters = clusters.rename(columns={"Resident_1": "ResidentialDemandTier1"})

    if "Resident_2" not in clusters:
        clusters["ResidentialDemandTier2"] = 43.8
    else:
        clusters = clusters.rename(columns={"Resident_2": "ResidentialDemandTier2"})

    if "Resident_3" not in clusters:
        clusters["ResidentialDemandTier3"] = 160.6
    else:
        clusters = clusters.rename(columns={"Resident_3": "ResidentialDemandTier3"})

    if "Resident_4" not in clusters:
        clusters["ResidentialDemandTier4"] = 423.4
    else:
        clusters = clusters.rename(columns={"Resident_4": "ResidentialDemandTier4"})

    if "Resident_5" not in clusters:
        clusters["ResidentialDemandTier5"] = 598.6
    else:
        clusters = clusters.rename(columns={"Resident_5": "ResidentialDemandTier5"})

    clusters["X_deg"] = clusters.geometry.centroid.x

    clusters["Y_deg"] = clusters.geometry.centroid.y

    clusters.to_file(workspace + r"\output.shp", driver='ESRI Shapefile')
    clusters.to_file(workspace + r"\output.csv", driver='CSV')
    print(datetime.datetime.now())
    return clusters