import unittest
import pandas as pd
import numpy as np
from os import listdir
from os.path import isfile, join
from Download_files import *
from Pathfinder_processing_steps import remove_grid_from_results_multiply_with_lenght, pathfinder_main
from Distribution import peakdemand_csv, transmission_matrix
from post_elec_GIS_functions import network_length

class ImportTestCase(unittest.TestCase):
    def test_all_grid_is_removed(self):
        """
        The test asserts that all cells that have a value below 0.5 is excluded from the total distribution lines for a 9 regions model
        :return:
        """
        i = 1
        dict_pathfinder = {}
        dict_weight = {}
        while i <2:
            name = str(i)
            electrified = pd.read_csv("../test_data/temp/dijkstra/elec_path_%s.csv" % (name), header=0 , index_col='Unnamed: 0')
            sum_one = electrified.sum()
            sum = sum_one.sum() #11638
            dict_pathfinder[name] = electrified
            weights = np.genfromtxt("../test_data/temp/dijkstra/%s_weight.csv" %(name), delimiter=',')
            weights_trimmed = weights[1:-1, 1:-1]
            weight_pandas = pd.DataFrame(weights_trimmed)
            dict_weight[name] = weight_pandas
            sum_before =+ sum
            i += 1
        tofolder = '../test_data/'
        remove_grid_from_results_multiply_with_lenght(dict_pathfinder, dict_weight, tofolder) #74 target should be removed
        distribution = pd.read_csv(os.path.join(tofolder, 'distributionlines.csv'))
        sum_after = distribution.loc[0]['0']
        assert sum_before - sum_after==74

    #def test_whole_pathfinder_process(self):
    #    path = '../test_data/Projected_files/'
    #    proj_path = '../test_data/temp/temp'
    #    elec_shp = '../test_data/Projected_files/elec.shp'
    #    tofolder = '../test_data/'
    #    pathfinder_main(path,proj_path, elec_shp, tofolder)
    #    assert 1==1

    def test_peakdemand(self):
        HV = '../test_data/run/HV_cells.csv'
        distribution_length_cell_ref = '../test_data/run/ref/distribution.csv'
        distribution = '../test_data/run/ref/distributionlines.csv'
        demand = '../test_data/run/ref/ref_demand.csv'
        specifieddemand = '../test_data/run/ref/demandprofile_rural.csv'
        capacitytoactivity = 31.536
        yearsplit = '../test_data/run/Demand/yearsplit.csv'
        reffolder = '../test_data/run/ref'
        distr_losses = 0.83

        peakdemand_csv(demand, specifieddemand, capacitytoactivity, yearsplit, distr_losses, HV, distribution,
                       distribution_length_cell_ref, reffolder)

        # error message in case if test case got failed
        results = pd.read_csv(os.path.join(reffolder,'peakdemand.csv'),index_col='Fuel')
        first = results.loc['TRLV_1_0', '2040']
        second = 0.54
        decimalPlace = 2
        self.assertAlmostEqual( first, second, decimalPlace)

    def test_transmissionlines_connection(self):
        topath = '../test_data/run/Demand'
        noHV = '../test_data/run/noHV_cells.csv'
        HV = '../test_data/run/HV_cells.csv'
        minigrid = '../test_data/run/elec_noHV_cells.csv'
        neartable = '../test_data/run/Demand/Near_table.csv'
        adjacencym = transmission_matrix(neartable, noHV, HV, minigrid, topath)
        self.assertTrue(len(adjacencym) == 656)

    def test_networklength_calculation(self):
        tofolder = '../test_data/run/ref'
        demandcells = '../test_data/run/Demand/demand_cells.csv'
        input = '../test_data/input/input_data.csv'
        demand = network_length(demandcells, input, tofolder)
        first = demand.loc['11', 'LV_km']
        second =2.66
        decimalPlace = 2
        self.assertAlmostEqual(first,second,decimalPlace)

if __name__ == '__main__':
    unittest.main()

