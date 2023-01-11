"""
Module: PV_battery_optimization
=============================

A module for optimising the PV and battery for each location. Returns the size of PV and hours of battery

---------------------------------------------------------------------------------------------------------------------------------------------

Module author: Nandi Moksnes <nandi@kth.se>
"""
from pulp import *
import pandas as pd
from datetime import timedelta
from matplotlib import pyplot as plt

def optimize_battery_pv(pv_power, location, load_profile, efficiency_discharge,  efficiency_charge, battery_constant, pv_cost, battery_cost):
    """
    This function optmize the PV+battery system based on the location specific capacity factor and load profile.
    The function returns the PV adjustment needed plus the required battery hours to meet the whole demand.
    The script is from the answer of AirSquid on March 16, 2022: 
    https://stackoverflow.com/questions/71494297/python-pulp-linear-optimisation-for-off-grid-pv-and-battery-system 
    The changes made are that the losses are accounted for discharging and charging
    """

    load = load_profile['Load']

    T = len(load)

    # Decision variables
    Bmax = LpVariable('Bmax', 0, None) # battery max energy (kWh)
    PV_size = LpVariable('PV_size', 0, None) # PV size
    batteryBin = LpVariable('BatteryBinary', cat='Binary')

    # Optimisation problem
    prb = LpProblem('Battery_Operation', LpMinimize)

    # Auxilliary variables
    PV_gen = [LpVariable('PVgen_{}'.format(i), 0, None) for i in range(T)]


    # Load difference
    Pflow = [LpVariable('Pflow_{}'.format(i), None, None) for i in range(T)]
    # Excess PV
    Pcharge = [LpVariable('Pcharge_{}'.format(i), lowBound=0, upBound=None) for i in range(T)]
    # Discharge required
    Pdischarge = [LpVariable('Pdischarge_{}'.format(i), lowBound=None, upBound=0) for i in range(T)]
    # Charge delivered
    Pcharge_a = [LpVariable('Pcharge_a{}'.format(i), 0, None) for i in range(T)]

    ###  Moved this down as it needs to include Pdischarge
    # Objective function
    # cost + some small penalty for cumulative discharge, just to shape behavior 
    prb += (PV_size*pv_cost) + (Bmax*battery_cost)- 0.01 * lpSum(Pdischarge[t] for t in range(T))

    # Battery
    Bstate = [LpVariable('E_{}'.format(i), 0, None) for i in range(T)]

    # Battery Constraints
    for t in range(1, T):
        prb += Bstate[t] == Bstate[t-1] + Pdischarge[t]*efficiency_discharge + Pcharge_a[t]*efficiency_charge 

    # Power flow Constraints
    for t in range(0, T):
        
        # PV generation
        prb += PV_gen[t] == PV_size*pv_power[location][t]
        
        # Pflow is the energy flow reuired *from the battery* to meet the load
        # Negative if load greater than PV, positive if PV greater than load
        prb += Pflow[t] == PV_gen[t] - load[t]
        
        # Given the below, it will push Pflow available for charge to zero or to to or greater than excess PV
        prb += Pcharge[t]*efficiency_charge  >= 0
        prb += Pcharge[t]*efficiency_charge >= Pflow[t]

        # If Pflow is negative (discharge), then it will at least Pflow discharge required load
        # If Pflow is positive (charge), then Pdischarge (discharge rePflowuired will ePflowual 0)
        prb += Pdischarge[t]*efficiency_discharge <= 0
        prb += Pdischarge[t]*efficiency_discharge <= Pflow[t]
        # Discharge cannot exceed available charge in battery
        # Discharge is negative
        prb += Pdischarge[t]*efficiency_discharge >= (-1)*Bstate[t-1]
        
        # Ensures that energy flow rePflowuired is satisifed by charge and discharge flows
        prb += Pflow[t] == Pcharge[t]*efficiency_charge + Pdischarge[t]*efficiency_discharge
        
        # Limit amount charge delivered by the available space in the battery
        prb += Pcharge_a[t]*efficiency_charge  >= 0
        prb += Pcharge_a[t]*efficiency_charge  <= Pcharge[t]
        prb += Pcharge_a[t]*efficiency_charge  <= Bmax - Bstate[t-1]
        
        prb += Bstate[t] >= 0
        prb += Bstate[t] <= Bmax

    # Solve problem
    prb.solve()

    # make some records to prep for dataframe (what a pain in pulp!!)
    res = []
    for t in range(T):
        record = {  'period': t,
                    'Load': load[t],
                    'PV_gen': PV_gen[t].varValue,
                    'Pflow' : Pflow[t].varValue,
                    'Pcharge': Pcharge[t].varValue,
                    'Pcharge_a': Pcharge_a[t].varValue,
                    'Pdischarge': Pdischarge[t].varValue,
                    'Bstate': Bstate[t].varValue}
        res.append(record)

    df = pd.DataFrame.from_records(res)
    df.set_index('period', inplace=True)
    df = df.round(2)
    print(df.to_string())

    print(f'PV size: {PV_size.varValue : 0.1f}, Batt size: {Bmax.varValue : 0.1f}')

    df.plot()
    plt.show()

    # write to a csv file
    output_filename = 'input_data/results_PuLP{}.csv'.format(location)

    # use a context manager to open/close the file...
    with open(output_filename, 'w') as fout:
        for v in prb.variables():
            line = ','.join([v.name, str(v.varValue)])   # make a string out of the elements, separated by commas
            #line2 = ','.join([model.name, str(model.objective)])
            fout.write(line)    # write the line to the file
            #fout.write(line2) 
            fout.write('\n')    # add a newline character

    return PV_size, Bstate

