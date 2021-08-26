"""
Module: Build_csv_files
=============================

A module for building the csv-files for GEOSeMOSYS https://github.com/KTH-dESA/GEOSeMOSYS to run that code
In this module the logic around electrified and un-electrified cells are implemented for the

----------------------------------------------------------------------------------------------------------------

Module author: Nandi Moksnes <nandi@kth.se>

"""

import pandas as pd
import geopandas as gpd
import sys
import os
import fnmatch
from geopandas.tools import sjoin

def renewableninja(path):
    """
    This function organize the data to the required format of a matrix with the
    location name on the x axis and hourly data on the y axis so that it can be fed into https://github.com/KTH-dESA/GEOSeMOSYS code
    the data is saved as capacityfactor_wind.csv and capacityfactor_solar.csv
    :param path:
    :return:
    """
    files = os.listdir(path)
    outwind = []
    outsolar = []
    for file in files:
        if fnmatch.fnmatch(file, '*out_wind*'):
            file = os.path.join(path,file)
            wind = pd.read_csv(file, index_col='time')
            outwind.append(wind)
    for file in files:
        if fnmatch.fnmatch(file, '*out_solar*'):
            file = os.path.join(path,file)
            solar = pd.read_csv(file, index_col='time')
            outsolar.append(solar)

    solarbase = pd.concat(outsolar, axis=1)
    windbase = pd.concat(outwind, axis=1)

    header = solarbase.columns
    new_header = [x.replace('X','') for x in header]
    solarbase.columns = new_header

    solarbase.drop('Unnamed: 0', axis='columns', inplace=True)
    solarbase.to_csv('run/data/capacityfactor_solar.csv')

    header = windbase.columns
    new_header = [x.replace('X','') for x in header]
    windbase.columns = new_header
    windbase.drop('Unnamed: 0', axis='columns', inplace=True)
    windbase.to_csv('run/data/capacityfactor_wind.csv')
    return()

def GIS_file():
    point = gpd.read_file('../Projected_files/new_40x40points_WGSUMT37S.shp')
    GIS_data = point['pointid']
    grid = pd.DataFrame(GIS_data, copy=True)
    grid.columns = ['Location']
    grid.to_csv('run/data/GIS_data.csv', index=False)
    return()

## Build files with elec/unelec aspects
def capital_cost_transmission_distrib(distribution_network, elec, un_elec_cells, transmission_near, capital_cost_HV, substation, capital_cost_LV):
    """Reads the transmission lines shape file, creates empty files for inputactivity, outputactivity, capitalcost for transmission lines, ditribution lines and diesel generators

    :param distribution_network: a shape file of the LV and MV infrastructure
    :param elec: are the 40*40m cells that have at least one cell of electrified 1x1km inside it
    :param un_elec_cells: are the 40*40m cells that have NO electrified cells 1x1km inside it
    :param transmission_near: Is the distance to closest HV line from the center of the 40*40 cell
    :param capital_cost_HV: kUSD/MW
    :param substation: kUSD/MW
    :param capital_cost_LV: kUSD/MW
    :return:
    """

    gdf = gpd.read_file(transmission_near)
    transm = pd.DataFrame(gdf)
    transm.index = transm['pointid']

    capitalcost = pd.DataFrame(columns=['Technology', 'Capitalcost'], index= range(0,10000)) # dtype = {'Technology':'object', 'Capitalcost':'float64'}

    inputactivity = pd.DataFrame(columns=['Column','Fuel','Technology','Inputactivity','ModeofOperation'])

    outputactivity = pd.DataFrame(columns=['Column','Fuel',	'Technology','Outputactivity','ModeofOperation'])

    elec = pd.read_csv(elec)
    un_elec = pd.read_csv(un_elec_cells)
    distribution = pd.read_excel(distribution_network)

    m = 0
    input_temp = []
    output_temp = []
    capital_temp = []

    ## Electrified cells
    for i in elec['elec']:

        capitalcost.loc[m]['Capitalcost'] = distribution.loc[i,'Tier2_LV_length_(km)']*capital_cost_LV + substation
        capitalcost.loc[m]['Technology'] = "TRLV_%i_1" %(i)

        h = len(inputactivity)
        input_temp = [0,"EL2_%i" %(i),"TRLV_%i_1" %(i), 1, 1]
        inputactivity.loc[h] = input_temp
        input_temp = []


        h = len(inputactivity)
        input_temp = [0, "KEEL2","KEEL00d_%i" %(i), 1, 1]
        inputactivity.loc[h] = input_temp
        input_temp = []


        h = len(inputactivity)
        input_temp = [0, "SOLAR_%i" %(i), "SOPV_%i_1" %(i), 1, 1]
        inputactivity.loc[h] = input_temp
        input_temp = []


        h = len(inputactivity)
        input_temp = [0, "SOLAR_%i" %(i), "SOPV8h_%i_1" %(i), 1, 1]
        inputactivity.loc[h] = input_temp
        input_temp = []


        h = len(inputactivity)
        input_temp = [0, "SOLAR_%i" %(i), "SOPV12h_%i_1" %(i), 1, 1]
        inputactivity.loc[h] = input_temp
        input_temp = []

        l = len(outputactivity)
        output_temp = [0, "EL3_%i_1" % (i), "EL3_%i_1" % (i), 0.865, 1]
        outputactivity.loc[l] = output_temp
        output_temp = []

        l = len(outputactivity)
        output_temp = [0, "EL3_%i_1" % (i), "KEEL00d_%i" % (i), 0.865, 1]
        outputactivity.loc[l] = output_temp
        output_temp = []

        l = len(outputactivity)
        output_temp = [0, "EL3_%i_1" % (i),  "SOPV12h_%i_1" % (i), 1, 1]
        outputactivity.loc[l] = output_temp
        output_temp = []

        l = len(outputactivity)
        output_temp = [0, "EL3_%i_1" % (i),  "SOPV8h_%i_1" % (i), 1, 1]
        outputactivity.loc[l] = output_temp
        output_temp = []

        l = len(outputactivity)
        output_temp = [0, "EL3_%i_1" % (i),  "SOPV_%i_1" % (i), 1, 1]
        outputactivity.loc[l] = output_temp
        output_temp = []

        m +=1

    ## Unelectrified cells
    for j in un_elec['unelec']:
        capitalcost.loc[m]['Capitalcost'] = transm.loc[j,'HV_dist']/1000*capital_cost_HV + substation  #kUSD/MW
        capitalcost.loc[m]['Technology'] = "TRHV_%i" %(j)
        m +=1
        capitalcost.loc[m]['Capitalcost'] = distribution.loc[j,'Tier2_LV_length_(km)']*capital_cost_LV + substation
        capitalcost.loc[m]['Technology'] = "TRLV_%i_0" %(j)

        h = len(inputactivity)
        input_temp = [0, "EL2_%i" %(j),"TRLV_%i_0" %(j), 1, 1]
        inputactivity.loc[h] = input_temp
        input_temp = []

        h = len(inputactivity)
        input_temp = [0, "SOLAR_%i" %(j),"SOPV_%i_0" %(j), 1, 1]
        inputactivity.loc[h] = input_temp
        input_temp = []

        h = len(inputactivity)
        input_temp = [0, "SOLAR_%i" %(j),"SOPV8h_%i_0" %(j), 1, 1]
        inputactivity.loc[h] = input_temp
        input_temp = []

        h = len(inputactivity)
        input_temp = [0, "SOLAR_%i" %(j),"SOPV12h_%i_0" %(j), 1, 1]
        inputactivity.loc[h] = input_temp
        input_temp = []

        h = len(inputactivity)
        input_temp = [0, "KEEL2_%i" %(j), "TRHV_%i" %(j), 1, 1]
        inputactivity.loc[h] = input_temp
        input_temp = []

        l = len(outputactivity)
        output_temp = [0,  "EL3_%i_0" % (j), "TRLV_%i_0" % (j), 0.865, 1]
        outputactivity.loc[l] = output_temp
        output_temp = []

        l = len(outputactivity)
        output_temp = [0,  "EL2_%i" % (j),"TRHV_%i" %(j), 1, 1]
        outputactivity.loc[l] = output_temp
        output_temp = []

        l = len(outputactivity)
        output_temp = [0,"EL3_%i_0" % (j),"SOPV12h_%i_0" % (j), 1, 1]
        outputactivity.loc[l] = output_temp
        output_temp = []

        l = len(outputactivity)
        output_temp = [0,"EL3_%i_0" % (j),"SOPV8h_%i_0" % (j), 1, 1]
        outputactivity.loc[l] = output_temp
        output_temp = []

        l = len(outputactivity)
        output_temp = [0,"EL3_%i_0" % (j),"SOPV_%i_0" % (j), 1, 1]
        outputactivity.loc[l] = output_temp
        output_temp = []

        l = len(outputactivity)
        output_temp = [0, "KEEL2_%i" % (j),"KEEL00t00", 0.95, 1]
        outputactivity.loc[l] = output_temp
        output_temp = []

        m += 1
    #For all cells
    for k in range(1,378):

        l = len(outputactivity)
        output_temp = [0,  "SOLAR_%i" % (k),"SO_%i" %(k), 1, 1]
        outputactivity.loc[l] = output_temp
        output_temp = []

        l = len(outputactivity)
        output_temp = [0,  "EL2_%i" % (k),"SOMG_%i" %(k), 1, 1]
        outputactivity.loc[l] = output_temp
        output_temp = []

        l = len(outputactivity)
        output_temp = [0,  "EL2_%i" % (k),"SOMG12h_%i" %(k), 1, 1]
        outputactivity.loc[l] = output_temp
        output_temp = []

        # outputactivity.loc[m]['Fuel'] = "EL2_%i" % (k)
        # outputactivity.loc[m]['Technology'] = "SOMG12h_%i" %(k)
        # outputactivity.loc[m]['Outputactivity'] = 1
        # outputactivity.loc[m]['ModeofOperation'] = 1

        l = len(outputactivity)
        output_temp = [0,  "EL2_%i" % (k),"WI_%i" %(k), 1, 1]
        outputactivity.loc[l] = output_temp
        output_temp = []


        l = len(outputactivity)
        output_temp = [0,  "EL2_%i" % (k), "KEDSGEN_%i" %(k), 1, 1]
        outputactivity.loc[l] = output_temp
        output_temp = []

        h = len(inputactivity)
        input_temp = [0, "SOLAR_%i" %(k), "SOMG_%i" %(k), 1, 1]
        inputactivity.loc[h] = input_temp
        input_temp = []

        h = len(inputactivity)
        input_temp = [0,  "KEDS", "KEDSGEN_%i" %(k), 4, 1]
        inputactivity.loc[h] = input_temp
        input_temp = []
        #The specific fuel consumption in a diesel generator is approximately 0.324 l/kWh when operating close to the rated power (approx. 70-89%) (Yamegueu et al., 2011).
        # However, there are variations depending on the load it operates under ranging from 0.32 to 0.53 l/kWh depending on the rated power (Dufo-López et al., 2011).
        #The Fuel Energy density is for Diesel 39.6 MJ/liter which leads to a fuel consumption of 12.672 MJ/kWh – 20.988 MJ/kWh. 1 kWh is 3.6 MJ meaning that 12.672/3.6 = 3.52 MJdiesel/MJel – 5.83 MJdiesel/MJel. 4 in the model.

        m +=1

    df1 = outputactivity['Fuel']
    df2 = inputactivity['Fuel']

    fuels = pd.concat([df1, df2]).drop_duplicates().reset_index(drop=True)
    tech1 = outputactivity['Technology']
    tech2 = inputactivity['Technology']
    technolgies = pd.concat([tech1, tech2]).drop_duplicates().reset_index(drop=True)

    df3 = outputactivity['Technology']
    df4 = inputactivity['Technology']

    technologies = pd.concat([df3, df4]).drop_duplicates().reset_index(drop=True)
    technologies.columns = 'Capacitytoactivity'


    capitalcost.to_csv('run/data/capitalcost.csv')
    inputactivity.to_csv('run/data/inputactivity.csv')
    outputactivity.to_csv('run/data/outputactivity.csv')
    technologies.to_csv('run/data/capacitytoactivity.csv')
    fuels.to_csv('run/data/fuels.csv')
    technolgies.to_csv('run/data/technologies.csv')

    return()

def near_dist(pop_shp, un_elec_cells, path):

    unelec = pd.read_csv(un_elec_cells)
    point = gpd.read_file(os.path.join(path, pop_shp))
    point.index = point['pointid']
    unelec_shp = gpd.GeoDataFrame()
    for i in unelec['unelec']:
        unelec_point = point.loc[i]
        unelec_shp = unelec_shp.append(unelec_point)

    lines = gpd.read_file(os.path.join(path, 'Concat_Transmission_lines_UMT37S.shp'))

    unelec_shp['HV_dist'] = unelec_shp.geometry.apply(lambda x: lines.distance(x).min())
    outpath = "run/Demand/transmission.shp"
    unelec_shp.to_file(outpath)

    return(outpath)

if __name__ == "__main__":
    #path = sys.argv[1]
    pop_shp = 'new_40x40points_WGSUMT37S.shp'
    un_elec_cells = 'run/un_elec_cells.csv'
    elec = 'run/elec_cells.csv'
    Projected_files_path = '../Projected_files/'
    distribution_network = 'run/Demand/Distribution_network.xlsx'

    capital_cost_HV = 2.5 #kUSD MW-km
    substation = 1.5 #kUSD/MW
    capital_cost_LV = 4 #kUSD/MW

    #renewableninja(path)
    #GIS_file()
    #transmission_near = "run/Demand/transmission.shp"
    transmission_near = near_dist(pop_shp, un_elec_cells, Projected_files_path)
    capital_cost_transmission_distrib(distribution_network, elec, un_elec_cells, transmission_near, capital_cost_HV, substation, capital_cost_LV)