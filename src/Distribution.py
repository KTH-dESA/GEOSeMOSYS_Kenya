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
    noHV = pd.read_csv(noHV_file)
    HV = pd.read_csv(HV_file)
    minigrid = pd.read_csv(minigridcsv)
    minigrid_no_grid = minigrid[~minigrid.pointid.isin(HV.pointid)]
    neartable = pd.read_csv(path)
    # The table includes the raw data from ArcMap function
    near_adj_points: Union[Union[Series, ExtensionArray, ndarray, DataFrame, None], Any] = neartable[neartable["DISTANCE"] > 0]

    near_adj_points.loc[(near_adj_points.SENDID.isin(HV.pointid)), 'SendTech'] = 'KEEL00t00'

    #add input fuel and inputtech to central exisiting grid
    central = near_adj_points.loc[(near_adj_points.SENDID.isin(HV.pointid))]
    central_nogrid = central.loc[central.NEARID.isin(noHV.pointid)]
    for m in central_nogrid.index:
        near_adj_points.loc[near_adj_points.index == m, 'INFUEL'] = 'KEEL2'
        near_adj_points.loc[(near_adj_points.index == m , 'INTECH')] = "TRHV_grid_" + str(int(near_adj_points.NEARID[m]))
        near_adj_points.loc[near_adj_points.index == m, 'OUTFUEL'] = "EL2_" + str(int(near_adj_points.NEARID[m]))

    central = near_adj_points.loc[(near_adj_points.SENDID.isin(HV.pointid))]

    central_minigrid = central.loc[central.NEARID.isin(minigrid_no_grid.pointid)]
    for m in central_minigrid.index:
        near_adj_points.loc[near_adj_points.index == m, 'INFUEL'] = 'KEEL2'
        near_adj_points.loc[(near_adj_points.index == m , 'INTECH')] = "TRHV_grid_" + str(int(near_adj_points.NEARID[m]))
        near_adj_points.loc[near_adj_points.index == m, 'OUTFUEL'] = "EL2_" + str(int(near_adj_points.NEARID[m]))

    df_tech = pd.DataFrame(columns=near_adj_points.columns,index=range(0,5000))
    #select where no inputfuel is present and their recieving cell has no HV in baseyear
    nan_intech = near_adj_points.loc[near_adj_points.INFUEL.isnull()]
    nan_intech_nogrid = nan_intech.loc[nan_intech.NEARID.isin(noHV.pointid)]
    #add input fuel to the (isnan INFUEL + isin noHV) selection
    m = 0
    for l in nan_intech_nogrid.index:
        near_adj_points.loc[near_adj_points.index == l, 'INFUEL'] = "EL2_" + str(int(near_adj_points.SENDID[l]))
        near_adj_points.loc[near_adj_points.index == l , 'INTECH'] = "TRHV_" + str(int(near_adj_points.SENDID[l])) + "_" + str(int(near_adj_points.NEARID[l]))
        near_adj_points.loc[near_adj_points.index == l, 'OUTFUEL'] = "EL2_" + str(int(near_adj_points.NEARID[l]))

        df_tech.loc[m, 'INFUEL'] = "EL2_" + str(int(near_adj_points.NEARID[l]))
        df_tech.loc[m , 'INTECH'] = "TRHV_" + str(int(near_adj_points.NEARID[l]))+ "_"+ str(int(near_adj_points.SENDID[l]))
        df_tech.loc[m, 'OUTFUEL'] = "EL2_" + str(int(near_adj_points.SENDID[l]))
        m += 1

    nan_intech_minigr = near_adj_points.loc[near_adj_points.INFUEL.isnull()]
    nan_intech_minigrid = nan_intech_minigr.loc[nan_intech_minigr.NEARID.isin(minigrid_no_grid.pointid)]
    #add input fuel to the (isnan INFUEL + isin noHV) selection

    for l in nan_intech_minigrid.index:
        near_adj_points.loc[near_adj_points.index == l, 'INFUEL'] = "EL2_" + str(int(near_adj_points.SENDID[l]))
        near_adj_points.loc[near_adj_points.index == l , 'INTECH'] = "TRHV_" + str(int(near_adj_points.SENDID[l])) + "_" + str(int(near_adj_points.NEARID[l]))
        near_adj_points.loc[near_adj_points.index == l, 'OUTFUEL'] = "EL2_" + str(int(near_adj_points.NEARID[l]))

        df_tech.loc[m, 'INFUEL'] = "EL2_" + str(int(near_adj_points.NEARID[l]))
        df_tech.loc[m , 'INTECH'] = "TRHV_" + str(int(near_adj_points.NEARID[l]))+ "_"+ str(int(near_adj_points.SENDID[l]))
        df_tech.loc[m, 'OUTFUEL'] = "EL2_" + str(int(near_adj_points.SENDID[l]))
        m += 1
    #
    #for i in noHV.pointid:
    #    near_adj_points.loc[near_adj_points.SENDID == i, 'SendTech'] = "TRHV_"+ str(int(i))
    #    near_adj_points.loc[near_adj_points.NEARID == i, 'ReceiveTech'] = "TRHV_" + str(int(i))

    #Allow for connections over cells with no population ("nan")
    not_grid = near_adj_points[~near_adj_points.SENDID.isin(HV.pointid)]
    nan = not_grid.loc[not_grid.INFUEL.isnull()]
    not_grid_reciever = nan[~nan.NEARID.isin(HV.pointid)]
    for j in not_grid_reciever.index:
        near_adj_points.loc[near_adj_points.index == j, 'INFUEL'] = "EL2_" + str(int(near_adj_points.SENDID[j]))
        near_adj_points.loc[near_adj_points.index == j , 'INTECH'] = "TRHV_" + str(int(near_adj_points.SENDID[j])) + "_" + str(int(near_adj_points.NEARID[j]))
        near_adj_points.loc[near_adj_points.index == j, 'OUTFUEL'] = "EL2_" + str(int(near_adj_points.NEARID[j]))

        df_tech.loc[m, 'INFUEL'] = "EL2_" + str(int(near_adj_points.NEARID[j]))
        df_tech.loc[m , 'INTECH'] = "TRHV_" + str(int(near_adj_points.NEARID[j]))+ "_"+ str(int(near_adj_points.SENDID[j]))
        df_tech.loc[m, 'OUTFUEL'] = "EL2_" + str(int(near_adj_points.SENDID[j]))
        m += 1

    df_tech_nan = df_tech.dropna(axis=0,how='all')
    nan_matrix = near_adj_points.loc[near_adj_points.INTECH.notnull()]

    #concat the two dataframes with the transmissionlines to one
    concat_matrices = pd.concat([nan_matrix, df_tech_nan], ignore_index=True)
    final_matrix = concat_matrices.drop(['OBJECTID *','INPUT_FID','NEAR_FID','NEARID','SENDID'], axis=1)
    final_matrix = final_matrix.drop_duplicates()

    final_matrix.to_csv(os.path.join(topath,'adjacencymatrix.csv'))
    return(os.path.join(topath,'adjacencymatrix.csv'))

