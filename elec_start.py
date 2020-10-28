#
# Author: KTH dESA Last modified by Nandi Moksnes
# Date: 2020-06
# Python version: 3.7
import os
from GIS_data_file import *
from onsset import *
import pandas as pd



#Inputdata that you need to define
specs_path = r"C:\Users\nandi\Box Sync\PhD\Paper 3-OSeMOSYS 40x40\Geosemosys\Kenya_electrification run\specsKenya.xlsx"
specs = pd.read_excel(specs_path, index_col=0)
settlements = r"C:\Users\nandi\Box Sync\PhD\Paper 3-OSeMOSYS 40x40\Geosemosys\Kenya_electrification run"
output_dir = r"C:\Users\nandi\Box Sync\PhD\Paper 3-OSeMOSYS 40x40\Geosemosys\Kenya_electrification run\output"
print('\n --- Prepping --- \n')


print("Kenya")
#settlements = base_dir # os.path.join(base_dir, '{}.csv'.format(country))
settlements_out_csv = output_dir + '.csv' # os.path.join(output_dir, '{}.csv'.format(country))

onsseter = SettlementProcessor(settlements_in)

onsseter.condition_df("Kenya")
onsseter.grid_penalties()
onsseter.calc_wind_cfs()

pop_actual = specs.loc["Kenya", SPE_POP]
pop_future = specs.loc["Kenya", SPE_POP_FUTURE]
urban_current = specs.loc["Kenya", SPE_URBAN]
urban_future = specs.loc["Kenya", SPE_URBAN_FUTURE]
urban_cutoff = specs.loc["Kenya", SPE_URBAN_CUTOFF]
start_year = int(specs.loc["Kenya", SPE_START_YEAR])
end_year = int(specs.loc["Kenya", SPE_END_YEAR])
time_step = int(specs.loc["Kenya", SPE_TIMESTEP])

elec_actual = specs.loc[country, SPE_ELEC]
pop_cutoff = specs.loc[country, SPE_POP_CUTOFF1]
min_night_lights = specs.loc[country, SPE_MIN_NIGHT_LIGHTS]
max_grid_dist = specs.loc[country, SPE_MAX_GRID_DIST]
max_road_dist = specs.loc[country, SPE_MAX_ROAD_DIST]
pop_tot = specs.loc[country, SPE_POP]
pop_cutoff2 = specs.loc[country, SPE_POP_CUTOFF2]
dist_to_trans = specs.loc[country, SPE_DIST_TO_TRANS]

urban_cutoff, urban_modelled = onsseter.calibrate_pop_and_urban(pop_actual, pop_future, urban_current,
                                                                urban_future, urban_cutoff, start_year, end_year, time_step)

min_night_lights, dist_to_trans, max_grid_dist, max_road_dist, elec_modelled, pop_cutoff, pop_cutoff2, rural_elec_ratio, urban_elec_ratio = \
    onsseter.elec_current_and_future(elec_actual, pop_cutoff, dist_to_trans, min_night_lights, max_grid_dist,
                                     max_road_dist, pop_tot, pop_cutoff2, start_year)

onsseter.grid_reach_estimate(start_year, gridspeed=9999)

specs.loc[country, SPE_URBAN_MODELLED] = urban_modelled
specs.loc[country, SPE_URBAN_CUTOFF] = urban_cutoff
specs.loc[country, SPE_MIN_NIGHT_LIGHTS] = min_night_lights
specs.loc[country, SPE_MAX_GRID_DIST] = max_grid_dist
specs.loc[country, SPE_MAX_ROAD_DIST] = max_road_dist
specs.loc[country, SPE_ELEC_MODELLED] = elec_modelled
specs.loc[country, SPE_POP_CUTOFF1] = pop_cutoff
specs.loc[country, SPE_POP_CUTOFF2] = pop_cutoff2
specs.loc[country, 'rural_elec_ratio'] = rural_elec_ratio
specs.loc[country, 'urban_elec_ratio'] = urban_elec_ratio


try:
    specs.to_excel(specs_path)
except ValueError:
    specs.to_excel(specs_path + '.xlsx')

onsseter.df.to_csv(settlements_out_csv, index=False)

def elec_current_and_future(self, elec_actual, pop_cutoff, dist_to_trans, min_night_lights,
                            max_grid_dist, max_road_dist, pop_tot, pop_cutoff2, start_year):
    """
    Calibrate the current electrification status, and future 'pre-electrification' status
    """
    urban_pop = (self.df.loc[self.df[SET_URBAN] == 2, SET_POP_CALIB].sum())  # Calibrate current electrification
    rural_pop = (self.df.loc[self.df[SET_URBAN] < 2, SET_POP_CALIB].sum())  # Calibrate current electrification
    total_pop = self.df[SET_POP_CALIB].sum()
    total_elec_ratio = elec_actual
    urban_elec_ratio = 0.98
    rural_elec_ratio = 0.393
    factor = (total_pop * total_elec_ratio) / (urban_pop * urban_elec_ratio + rural_pop * rural_elec_ratio)
    urban_elec_ratio *= factor
    rural_elec_ratio *= factor
    # print('factor: ' + str(factor))

    logging.info('Calibrate current electrification')
    is_round_two = False
    grid_cutoff2 = 5
    road_cutoff2 = 5
    count = 0
    prev_vals = []
    accuracy = 0.01
    max_iterations_one = 30
    max_iterations_two = 60
    # self.df[SET_ELEC_CURRENT] = 0

    # if max(self.df['TransformerDist']) > 0:
    #    self.df['GridDistCalibElec'] = self.df['TransformerDist']
    #    priority = 1
    # elif max(self.df['CurrentMVLineDist']) > 0:
    #    self.df['GridDistCalibElec'] = self.df['CurrentMVLineDist']
    #    priority = 1
    # else:
    #    self.df['GridDistCalibElec'] = self.df['CurrentHVLineDist']
    #    priority = 2
    #
    #
    # condition = 0
    # while condition == 0:
    #     # Assign the 1 (electrified)/0 (un-electrified) values to each cell
    #     # urban_electrified = 0.159853988426699 * 17573607 * 0.487
    #     urban_electrified = urban_pop * urban_elec_ratio
    #     # urban_electrified = urban_electrified_modelled * self.df[SET_POP_CALIB].sum() * urban_elec_access
    #     # rural_electrified = (1 - 0.159853988426699) * 17573607 * 0.039
    #     rural_electrified = rural_pop * rural_elec_ratio
    #     # rural_electrified = (1 - urban_electrified_modelled) * self.df[SET_POP_CALIB].sum() * rural_elec_access
    #     if priority == 1:
    #         self.df.loc[(self.df['GridDistCalibElec'] < 15) & (self.df[SET_NIGHT_LIGHTS] > 0) & (self.df[SET_POP_CALIB] > 5), SET_ELEC_CURRENT] = 1
    #         # self.df.loc[(self.df[SET_NIGHT_LIGHTS] > 0) & (self.df[SET_POP_CALIB] > 50), SET_ELEC_CURRENT] = 1
    #         # self.df.loc[(self.df['GridDistCalibElec'] < 0.8), SET_ELEC_CURRENT] = 1
    #         urban_elec_ratio = urban_electrified / (self.df.loc[(self.df[SET_ELEC_CURRENT] == 1) & (self.df[SET_URBAN] == 2), SET_POP_CALIB].sum())
    #         rural_elec_ratio = rural_electrified / (self.df.loc[(self.df[SET_ELEC_CURRENT] == 1) & (self.df[SET_URBAN] < 2), SET_POP_CALIB].sum())
    #         pop_elec = self.df.loc[self.df[SET_ELEC_CURRENT] == 1, SET_POP_CALIB].sum()
    #         elec_modelled = pop_elec / pop_tot
    #     else:
    #         self.df.loc[(self.df[SET_NIGHT_LIGHTS] > 0) & (self.df['GridDistCalibElec'] < 5) |  | (self.df[SET_POP_CALIB] > 7000) | (self.df[SET_ROAD_DIST]<3), SET_ELEC_CURRENT] = 1
    #         # self.df.loc[(self.df['GridDistCalibElec'] < 0.8), SET_ELEC_CURRENT] = 1
    #         urban_elec_ratio = (self.df.loc[(self.df[SET_ELEC_CURRENT] == 1) & (
    #                     self.df[SET_URBAN] == 2), SET_POP_CALIB].sum()) / urban_electrified
    #         rural_elec_ratio = (self.df.loc[(self.df[SET_ELEC_CURRENT] == 1) & (
    #                     self.df[SET_URBAN] < 2), SET_POP_CALIB].sum()) / rural_electrified
    #         pop_elec = self.df.loc[self.df[SET_ELEC_CURRENT] == 1, SET_POP_CALIB].sum()
    #         elec_modelled = pop_elec / pop_tot

    while True:
        self.df[SET_ELEC_CURRENT] = self.df.apply(lambda row:
                                                  1
                                                  if ((row[SET_NIGHT_LIGHTS] > 0 or
                                                       row[SET_POP_CALIB] > pop_cutoff and
                                                       row['CurrentHVLineDist'] < max_grid_dist or
                                                       row[SET_ROAD_DIST] < max_road_dist))
                                                  # or (row[SET_POP_CALIB] > pop_cutoff2 and
                                                  # (row['CurrentHVLineDist'] < grid_cutoff2 or
                                                  # row[SET_ROAD_DIST] < road_cutoff2))
                                                  else 0, axis=1)

        # Get the calculated electrified ratio, and limit it to within reasonable boundaries
        pop_elec = self.df.loc[self.df[SET_ELEC_CURRENT] == 1, SET_POP_CALIB].sum()
        elec_modelled = pop_elec / pop_tot

        if elec_modelled == 0:
            elec_modelled = 0.01
        elif elec_modelled == 1:
            elec_modelled = 0.99

        if abs(elec_modelled - elec_actual) < accuracy:
            break
        elif not is_round_two:
            min_night_lights = \
            sorted([0, min_night_lights - min_night_lights * 2 * (elec_actual - elec_modelled) / elec_actual, 1])[1]
            pop_cutoff = \
            sorted([0.01, pop_cutoff - pop_cutoff * 0.5 * (elec_actual - elec_modelled) / elec_actual, 100000])[1]
            max_grid_dist = \
            sorted([0.5, max_grid_dist + max_grid_dist * 2 * (elec_actual - elec_modelled) / elec_actual, 60])[1]
            max_road_dist = \
            sorted([0.5, max_road_dist + max_road_dist * 2 * (elec_actual - elec_modelled) / elec_actual, 5])[1]
        elif elec_modelled - elec_actual < 0:
            pop_cutoff2 = sorted([0.01, pop_cutoff2 - pop_cutoff2 *
                                  (elec_actual - elec_modelled) / elec_actual, 100000])[1]
        elif elec_modelled - elec_actual > 0:
            pop_cutoff = sorted([0.01, pop_cutoff - pop_cutoff * 0.5 *
                                 (elec_actual - elec_modelled) / elec_actual, 10000])[1]
            #
        constraints = '{}{}{}{}{}'.format(pop_cutoff, min_night_lights, max_grid_dist, max_road_dist, pop_cutoff2)
        if constraints in prev_vals and not is_round_two:
            logging.info('Repeating myself, on to round two')
            prev_vals = []
            is_round_two = True
        elif constraints in prev_vals and is_round_two:
            logging.info('NOT SATISFIED: repeating myself')
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
            logging.info('Got to {}, on to round two'.format(max_iterations_one))
            is_round_two = True
        elif count >= max_iterations_two and is_round_two:
            logging.info('NOT SATISFIED: Got to {}'.format(max_iterations_two))
            print('2. Modelled electrification rate = {}'.format(elec_modelled))
            if 'y' in input('Do you want to rerun calibration with new input values? <y/n>'):
                count = 0
                is_round_two = False
                pop_cutoff = int(input('Enter value for pop_cutoff: '))
                min_night_lights = int(input('Enter value for min_night_lights: '))
                max_grid_dist = int(input('Enter value for max_grid_dist: '))
                max_road_dist = int(input('Enter value for max_road_dist: '))
                pop_cutoff2 = int(input('Enter value for pop_cutoff2: '))
            else:
                break

        count += 1
        rural_elec_ratio = 1
        urban_elec_ratio = 1

    logging.info('The modelled electrification rate achieved is {}. '
                 'If this is not acceptable please revise this part of the algorithm'.format(elec_modelled))
    condition = 1

    self.df[SET_ELEC_FUTURE_GRID + "{}".format(start_year)] = \
        self.df.apply(lambda row: 1 if row[SET_ELEC_CURRENT] == 1 else 0, axis=1)
    self.df[SET_ELEC_FUTURE_OFFGRID + "{}".format(start_year)] = self.df.apply(lambda row: 0, axis=1)
    self.df[SET_ELEC_FUTURE_ACTUAL + "{}".format(start_year)] = \
        self.df.apply(lambda row: 1 if row[SET_ELEC_FUTURE_GRID + "{}".format(start_year)] == 1 or
                                       row[SET_ELEC_FUTURE_OFFGRID + "{}".format(start_year)] == 1 else 0, axis=1)
    self.df[SET_ELEC_FINAL_CODE + "{}".format(start_year)] = \
        self.df.apply(lambda row: 1 if row[SET_ELEC_CURRENT] == 1 else 99, axis=1)

    return min_night_lights, dist_to_trans, max_grid_dist, max_road_dist, elec_modelled, pop_cutoff, pop_cutoff2, rural_elec_ratio, urban_elec_ratio