"""
Module: elec_start
=============================

A module that estimates the
---------------------------------------------------------------------------------------------

Module author: KTH-dES modified by Nandi Moksnes

"""

# Author: KTH dESA Last modified by Nandi Moksnes
# Date: 2021-04
# Python version: 3.8
import os
import sys
import pandas as pd
import geopandas as gpd


def calibrate_pop_and_urban(settlement, pop_actual, urban, urban_cutoff):
    """
    Calibrate the actual current population, the urban split and forecast the future population
    """
    # Calculate the ratio between the actual population and the total population from the GIS layer
    print('Calibrate current population')
    pop_ratio = pop_actual / settlement['grid_code'].sum()

    # And use this ratio to calibrate the population in a new column
    settlement['pop'] = settlement.apply(lambda row: row['grid_code'] * pop_ratio, axis=1)

    # Calculate the urban split, by calibrating the cutoff until the target ratio is achieved
    # Keep looping until it is satisfied or another break conditions is reached
    print('Calibrate urban split')
    count = 0
    prev_vals = []  # Stores cutoff values that have already been tried to prevent getting stuck in a loop
    accuracy = 0.005
    max_iterations = 30
    urban_modelled = 0
    while True:
        # Assign the 1 (urban)/0 (rural) values to each cell
        settlement['urban'] = settlement.apply(lambda row: 1 if row['pop'] > urban_cutoff else 0, axis=1)

        # Get the calculated urban ratio, and limit it to within reasonable boundaries
        pop_urb = settlement.loc[settlement['urban'] == 1, 'pop'].sum()
        urban_modelled = pop_urb / pop_actual

        if urban_modelled == 0:
            urban_modelled = 0.05
        elif urban_modelled == 1:
            urban_modelled = 0.999

        if abs(urban_modelled - urban) < accuracy:
            break
        else:
            urban_cutoff = sorted([0.005, urban_cutoff - urban_cutoff * 2 *
                                   (urban - urban_modelled) / urban, 10000.0])[1]

        if urban_cutoff in prev_vals:
            print('NOT SATISFIED: repeating myself')
            break
        else:
            prev_vals.append(urban_cutoff)

        if count >= max_iterations:
            print('NOT SATISFIED: got to {}'.format(max_iterations))
            break

        count += 1
    #settlement.to_csv("../Projected_files/urban_pop_calibrated.csv")
    return settlement


def elec_current_and_future(settlement, elec_actual, pop_cutoff, dist_to_trans, dist_to_sub, dist_minig, min_night_lights,
                            max_grid_dist, urban_elec_ratio, rural_elec_ratio, max_road_dist, pop_actual, pop_cutoff2, start_year):
    """This function calibrate the current electrification status, and future 'pre-electrification' status
    :param settlement:
    :param elec_actual:
    :param pop_cutoff:
    :param dist_to_trans:
    :param dist_to_sub:
    :param dist_minig:
    :param min_night_lights:
    :param max_grid_dist:
    :param urban_elec_ratio:
    :param rural_elec_ratio:
    :param max_road_dist:
    :param pop_actual:
    :param pop_cutoff2:
    :param start_year:
    :return:
    """
    urban_pop = (settlement.loc[settlement['urban'] == 1, 'pop'].sum())  # Calibrate current electrification
    rural_pop = (settlement.loc[settlement['urban'] < 1, 'pop'].sum())  # Calibrate current electrification
    total_pop = settlement['pop'].sum()
    total_elec_ratio = elec_actual
    factor = (total_pop * total_elec_ratio) / (urban_pop * urban_elec_ratio + rural_pop * rural_elec_ratio)
    urban_elec_ratio *= factor
    rural_elec_ratio *= factor

    print('Calibrate current electrification')
    is_round_two = False
    grid_cutoff2 = 50000
    road_cutoff2 = 5000
    count = 0
    prev_vals = []
    accuracy = 0.01
    max_iterations_one = 30
    max_iterations_two = 60

    while True:
        settlement['elec'] = settlement.apply(lambda row:
                                                  1
                                                  if (row['Nighttime'] > min_night_lights and
                                                       (row['Minigrid'] < dist_minig or
                                                       row['Grid'] < max_grid_dist and
                                                        (row['Transform'] < dist_to_trans or
                                                       row['Substation'] < dist_to_sub or
                                                       row['Road'] < max_road_dist or
                                                       row['pop'] > pop_cutoff)))
                                                   or (row['pop'] > pop_cutoff2 and
                                                   (row["Grid"] < grid_cutoff2 or
                                                   row["Road"] < road_cutoff2))
                                                  else 0, axis=1)

        # Get the calculated electrified ratio, and limit it to within reasonable boundaries
        pop_elec = settlement.loc[settlement['elec'] == 1, 'pop'].sum()
        elec_modelled = pop_elec / total_pop
        print(elec_modelled)

        if elec_modelled == 0:
            elec_modelled = 0.01
        elif elec_modelled == 1:
            elec_modelled = 0.99

        if abs(elec_modelled - elec_actual) < accuracy:
            break
        elif not is_round_two:
            min_night_lights = \
            sorted([0, min_night_lights - min_night_lights * 0.5 * (elec_actual - elec_modelled) / elec_actual, 150])[1]
            pop_cutoff = \
            sorted([200, pop_cutoff - pop_cutoff *2* (elec_actual - elec_modelled) / elec_actual, 10000])[1]
            max_grid_dist = \
            sorted([500, max_grid_dist + max_grid_dist *2* (elec_actual - elec_modelled) / elec_actual, 20000])[1]
            max_road_dist = \
            sorted([500, max_road_dist + max_road_dist * 0.5 * (elec_actual - elec_modelled) / elec_actual, 3000])[1]
            dist_minig = \
            sorted([100, dist_minig - dist_minig  * (elec_actual - elec_modelled) / elec_actual, 5000])[1]
            dist_to_trans = \
            sorted([100, dist_to_trans - dist_to_trans * (elec_actual - elec_modelled) / elec_actual, 5000])[1]
            dist_to_sub = \
            sorted([500, dist_to_sub + dist_to_sub * (elec_actual - elec_modelled) / elec_actual, 30000])[1]
        elif elec_modelled - elec_actual < 0:
            pop_cutoff2 = sorted([0.01, pop_cutoff2 - pop_cutoff2 *
                                  (elec_actual - elec_modelled) / elec_actual, 100000])[1]
        elif elec_modelled - elec_actual > 0:
            pop_cutoff = sorted([0.01, pop_cutoff - pop_cutoff * 0.5 *
                                 (elec_actual - elec_modelled) / elec_actual, 10000])[1]
            #
        constraints = '{}{}{}{}{}'.format(pop_cutoff, min_night_lights, max_grid_dist, max_road_dist, pop_cutoff2)
        if constraints in prev_vals and not is_round_two:
            print('Repeating myself, on to round two')
            prev_vals = []
            is_round_two = True
        elif constraints in prev_vals and is_round_two:
            print('NOT SATISFIED: repeating myself')
            print('2. Modelled electrification rate = {}'.format(elec_modelled))
            if 'y' in input('Do you want to rerun calibration with new input values? <y/n>'):
                count = 0
                is_round_two = False
                pop_cutoff = float(input('Enter value for pop_cutoff: '))
                min_night_lights = float(input('Enter value for min_night_lights: '))
                max_grid_dist = float(input('Enter value for max_grid_dist: '))
                max_road_dist = float(input('Enter value for max_road_dist: '))
                pop_cutoff2 = float(input('Enter value for pop_cutoff2: '))
                break
        else:
            prev_vals.append(constraints)

        if count >= max_iterations_one and not is_round_two:
            print('Got to {}, on to round two'.format(max_iterations_one))
            is_round_two = True
        elif count >= max_iterations_two and is_round_two:
            print('NOT SATISFIED: Got to {}'.format(max_iterations_two))
            print('2. Modelled electrification rate = {}'.format(elec_modelled))
            if 'y' in input('Do you want to rerun calibration with new input values? <y/n>'):
                count = 0
                is_round_two = False
                pop_cutoff = int(input('Enter value for pop_cutoff: '))
                min_night_lights = float(input('Enter value for min_night_lights: '))
                max_grid_dist = int(input('Enter value for max_grid_dist: '))
                max_road_dist = int(input('Enter value for max_road_dist: '))
                pop_cutoff2 = int(input('Enter value for pop_cutoff2: '))
            else:
                break

        count += 1
        rural_elec_ratio = 1
        urban_elec_ratio = 1

    print('The modelled electrification rate achieved is {}. '
                 'If this is not acceptable please revise this part of the algorithm'.format(elec_modelled))
    condition = 1

    print("nightlight:", min_night_lights, "Transformers:", dist_to_trans, "Substations:", dist_to_sub, "Grid:", max_grid_dist, "Road", max_road_dist, "Elec:", elec_modelled, "pop_threshold:", pop_cutoff)
    gdf = gpd.GeoDataFrame(settlement, geometry=settlement.geometry, crs=32737)
    gdf.to_file("../Projected_files/elec.shp")
    settlement.to_csv("../Projected_files/elec.csv")

    return


if __name__ == "__main__":
    pop_shp = '../Projected_files/settlements.shp'
    Projected_files_path = '../Projected_files/'
    #from settlement_build import *

    #points = raster_to_point(pop_shp, Projected_files_path)
    #point_line = near_calculations_line(points, Projected_files_path)
    #settlements = near_calculations_point(point_line, Projected_files_path)
    #settlements
    #settlements = sys.argv[1]
    elec_actual = 0.75  # percent
    pop_cutoff = 350  # people
    dist_to_trans = 5000  # meters
    dist_to_sub = 5000
    min_night_lights = 1
    max_grid_dist = 50000  # meters
    max_road_dist = 2000  # meters
    dist_minig = 3000 #meters
    pop_cutoff2 = 1000  # people
    urban_elec_ratio = 83.5  # percent
    rural_elec_ratio = 71.5  # percent
    pop_actual = 52570000  # peolpe
    urban = 0.275  # percent
    urban_cutoff = 20000
    start_year = 2018
    settlement = gpd.read_file(pop_shp)
    settlements = pd.DataFrame(settlement, copy=True)
    urbansettlements = calibrate_pop_and_urban(settlements, pop_actual, urban, urban_cutoff)
    elec_current_and_future(urbansettlements, elec_actual, pop_cutoff, dist_to_trans, dist_to_sub, dist_minig, min_night_lights,
                            max_grid_dist, urban_elec_ratio, rural_elec_ratio, max_road_dist, pop_actual, pop_cutoff2, start_year)