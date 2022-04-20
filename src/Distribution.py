"""
Module: Distribution
=============================

A module for building the distribution specific csv files for GEOSeMOSYS https://github.com/KTH-dESA/GEOSeMOSYS to run that code
In this module the logic around peakdemand, transmissionlines and distributionlines are built.

---------------------------------------------------------------------------------------------------------------------------------------------

Module author: Nandi Moksnes <nandi@kth.se>

"""
import pandas as pd
import os
pd.options.mode.chained_assignment = None
from typing import Any, Union
from numpy import ndarray
from pandas import Series, DataFrame
from pandas.core.arrays import ExtensionArray

def transmission_matrix(path, noHV_file, HV_file, minigridcsv, topath):
    """
    This function creates transmissionlines in both directions for each cell and connects the adjacent cells to grid to the central grid.
    :param path:
    :param noHV_file:
    :param HV_file:
    :param minigridcsv:
    :param topath:
    :return:
    """
    noHV = pd.read_csv(noHV_file)
    HV = pd.read_csv(HV_file)
    minigrid = pd.read_csv(minigridcsv)
    neartable = pd.read_csv(path)
    # The table includes the raw data from ArcMap function
    near_adj_points: Union[Union[Series, ExtensionArray, ndarray, DataFrame, None], Any] = neartable[neartable["DISTANCE"] > 0]

    near_adj_points.loc[(near_adj_points.SENDID.isin(HV.pointid)), 'SendTech'] = 'KEEL00t00'

    #add input fuel and inputtech to central exisiting grid
    central = near_adj_points.loc[(near_adj_points.SENDID.isin(HV.pointid))]
    central_nogrid = central.loc[central.NEARID.isin(noHV.pointid)]
    for m in central_nogrid.index:
        near_adj_points.loc[near_adj_points.index == m, 'INFUEL'] = 'KEEL2'
        near_adj_points.loc[(near_adj_points.index == m , 'INTECH')] =  "TRHV_"+ str(int(near_adj_points.SENDID[m])) + "_" + str(int(near_adj_points.NEARID[m]))
        near_adj_points.loc[near_adj_points.index == m, 'OUTFUEL'] = "EL2_" + str(int(near_adj_points.NEARID[m]))

    central = near_adj_points.loc[(near_adj_points.SENDID.isin(HV.pointid))]

    central_minigrid = central.loc[central.NEARID.isin(minigrid.pointid)]
    for m in central_minigrid.index:
        near_adj_points.loc[near_adj_points.index == m, 'INFUEL'] = 'KEEL2'
        near_adj_points.loc[(near_adj_points.index == m , 'INTECH')] = "TRHV_"+ str(int(near_adj_points.SENDID[m])) + "_" + str(int(near_adj_points.NEARID[m]))
        near_adj_points.loc[near_adj_points.index == m, 'OUTFUEL'] = "EL2_" + str(int(near_adj_points.NEARID[m]))

    #select where no inputfuel is present and their recieving cell has no HV in baseyear
    nan_intech = near_adj_points.loc[near_adj_points.INFUEL.isnull()]
    nan_intech_nogrid = nan_intech.loc[nan_intech.NEARID.isin(noHV.pointid)]
    #add input fuel to the (isnan INFUEL + isin noHV) selection
    m = 0
    for l in nan_intech_nogrid.index:
        near_adj_points.loc[near_adj_points.index == l, 'INFUEL'] = "EL2_" + str(int(near_adj_points.SENDID[l]))
        near_adj_points.loc[near_adj_points.index == l , 'INTECH'] = "TRHV_" + str(int(near_adj_points.SENDID[l])) + "_" + str(int(near_adj_points.NEARID[l]))
        near_adj_points.loc[near_adj_points.index == l, 'OUTFUEL'] = "EL2_" + str(int(near_adj_points.NEARID[l]))

    nan_intech_minigr = near_adj_points.loc[near_adj_points.INFUEL.isnull()]
    nan_intech_minigrid = nan_intech_minigr.loc[nan_intech_minigr.NEARID.isin(minigrid.pointid)]
    #add input fuel to the (isnan INFUEL + isin noHV) selection

    for l in nan_intech_minigrid.index:
        near_adj_points.loc[near_adj_points.index == l, 'INFUEL'] = "EL2_" + str(int(near_adj_points.SENDID[l]))
        near_adj_points.loc[near_adj_points.index == l , 'INTECH'] = "TRHV_" + str(int(near_adj_points.SENDID[l])) + "_" + str(int(near_adj_points.NEARID[l]))
        near_adj_points.loc[near_adj_points.index == l, 'OUTFUEL'] = "EL2_" + str(int(near_adj_points.NEARID[l]))

    #Allow for connections over cells with no population ("nan")
    not_grid = near_adj_points[~near_adj_points.SENDID.isin(HV.pointid)]
    nan = not_grid.loc[not_grid.INFUEL.isnull()]
    not_grid_reciever = nan[~nan.NEARID.isin(HV.pointid)]
    for j in not_grid_reciever.index:
        near_adj_points.loc[near_adj_points.index == j, 'INFUEL'] = "EL2_" + str(int(near_adj_points.SENDID[j]))
        near_adj_points.loc[near_adj_points.index == j , 'INTECH'] = "TRHV_" + str(int(near_adj_points.SENDID[j])) + "_" + str(int(near_adj_points.NEARID[j]))
        near_adj_points.loc[near_adj_points.index == j, 'OUTFUEL'] = "EL2_" + str(int(near_adj_points.NEARID[j]))

    nan_matrix = near_adj_points.loc[near_adj_points.INTECH.notnull()]
    #concat the two dataframes with the transmissionlines to one
    final_matrix = nan_matrix.drop(['OBJECTID *','INPUT_FID','NEAR_FID','NEARID','SENDID'], axis=1)
    final_matrix = final_matrix.drop_duplicates()

    final_matrix.to_csv(os.path.join(topath,'adjacencymatrix.csv'))

def peakdemand_csv(demand_csv, specifieddemand,capacitytoactivity, yearsplit_csv, distr_losses, distributionlines_file, distributioncelllength_file, tofolder):
    """
    This function calculates the peakdemand per year and demand. This is used to calculate the kW/km in the next step.
    :param demand:
    :param specifieddemand:
    :param capacitytoactivity:
    :return:
    """
    profile = pd.read_csv(specifieddemand,index_col='Timeslice', header=0)
    demand = pd.read_csv(demand_csv, index_col='Fuel', header=0)
    yearsplit = pd.read_csv(yearsplit_csv, index_col='Timeslice', header=0)
    distributionlines = pd.read_csv(distributionlines_file)
    distributioncelllength= pd.read_csv(distributioncelllength_file)

    #The peakdemand is defined as the peak demand over km per cell
    # Peakdemand = max(specifiedannualdemand*specifieddemandprofile/(capacitytoactivityunit*yearsplit))/km_cell

    demand_capacitytoact = demand.apply(lambda row: row/capacitytoactivity,axis=1)
    profile_yearsplit = profile.divide(yearsplit)
    #I take the max of all years as the max decrease in 2030 in the Kenya case. This is to make sure that there is always capacity in OSemOSYS
    max_share_peryear = (profile_yearsplit.max().max())/distr_losses

    peak_demand_all = demand_capacitytoact.apply(lambda row: row * max_share_peryear, axis=1)
    peakdemand = peak_demand_all.loc[peak_demand_all.index.str.endswith('_0', na=False)]
    peakdemand.index = peakdemand.index.str.replace('EL3','TRLV')


    distributionlines = distributionlines.set_index(distributionlines.iloc[:, 0])
    distribution = distributionlines.drop(columns ='Unnamed: 0')

    distributioncelllength.index = distributioncelllength['pointid']
    distribtionlength = distributioncelllength.drop(['Unnamed: 0', 'pointid', 'elec'], axis = 1)

    distribution_total = distribution.multiply(distribtionlength.LV_km, axis = "rows")
    ## TODO divide per cell the km that are defined in distribution_total
    ## TODO add peakdemand TRLVM as well to cover the demand

    peakdemand.to_csv(os.path.join(tofolder,'peakdemand.csv'))

