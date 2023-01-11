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

def optimize_battery_pv(pv_power, location, load_profile, efficiency_discharge,  efficiency_charge, power, pv_cost, battery_cost):
    """
    This function optmize the PV+battery system based on the location specific capacity factor and load profile.
    The function returns the PV adjustment needed plus the required battery hours to meet the whole demand.
    The script is from the answer of AirSquid on March 16, 2022: 
    https://stackoverflow.com/questions/71494297/python-pulp-linear-optimisation-for-off-grid-pv-and-battery-system 
    The changes made are that the losses are accounted for dischargin and charging
    """
    
    # p_df = pd.DataFrame(columns=['charging', 'discharging', 'PVtoload', 'kWh'],index=load_profile.index.copy())
    # p_df_power = pd.merge(p_df, pv_power, left_index=True, right_index=True)
    # p_df_all = pd.merge(p_df_power, load_profile, left_index=True, right_index=True)

    # p_df_all = p_df_all.reset_index()

    load = load_profile['Load']

    T = len(load)

    # Decision variables
    Bmax = LpVariable('Bmax', 0, None) # battery max energy (kWh)
    PV_size = LpVariable('PV_size', 0, None) # PV size

    # Optimisation problem
    prb = LpProblem('Battery_Operation', LpMinimize)

    # Auxilliary variables
    PV_gen = [LpVariable('PV_gen_{}'.format(i), 0, None) for i in range(T)]

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
    prb += (PV_size*pv_cost) + (Bmax*battery_cost)  - 0.01 * lpSum(Pdischarge[t] for t in range(T)) 

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

        # If Pflow is negative (discharge), then it will at least ePflowual discharge rePflowuired
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

    # model = LpProblem("PV_Battery_problem", LpMinimize)
    # # # modes = { 'Charging'    : 1, 
    # # #  'Discharging'      : 1}
    # time = len(p_df_all.index)
    # #N = range (time) #time dimension
    # # N_1 = range(time+1)
    # # # M = modes.keys()   #
    # # # NM = {(n,m) for n in N for m in M}

    # #Decision variables
    # PV_adjustment = LpVariable("PVAdjustment{}".format(location), lowBound=0, upBound=None)
    # battery_hours = LpVariable("BatteryHours{}".format(location), lowBound=0, upBound=None)

    # #power flow variables
    # PV_kw = [LpVariable('PVkWh{}'.format(i), lowBound=None, upBound=0) for i in range(time)]
    # #load = LpVariable.dicts("Load{}".format(location),N, 0 ,100000, LpContinuous)
    # charging_a = [LpVariable("ChargingBattery{}".format(i), lowBound=0, upBound=None) for i in range(time)]
    # charging = [LpVariable("Charging{}".format(i), lowBound=0, upBound=None) for i in range(time)]
    # discharging = [LpVariable("Disharging{}".format(i), lowBound=None, upBound=0) for i in range(time)]
    # BatteryLevel = [LpVariable("Batterylevel{}".format(i), lowBound=0, upBound=None) for i in range(time)]
    # #chargeswitch = LpVariable.dicts("Binarycharge{}".format(location),indexs= N, cat='Binary')
    # #dischargeswitch = LpVariable.dicts("Binarydischarge{}".format(location),indexs= N, cat='Binary')
    # delta = [LpVariable("DeltaValue{}".format(i), lowBound=0, upBound=None)for i in range(time)]
    # #balancingovershoot = LpVariable.dicts("BalancingBattery{}".format(location),indexs= N, cat='Continuous')
    # #y1 = LpVariable.dicts("chargingY{}".format(location), N, cat='Continuous')
    # #y2 = LpVariable.dicts("dischargingY{}".format(location), N, cat='Continuous')
    
    # # #OBJECTIVE FUNCTION
    # model += (pv_cost * PV_adjustment) + (battery_cost*battery_hours), "System cost{}".format(location) 
    # BatteryLevel[0] == battery_hours*power

    # for t in range(1, time):
    #      model += BatteryLevel[t] == BatteryLevel[t-1] + discharging[t] + charging_a[t] 


    # # # Power flow Constraints
    # for t in range(0, time):
        
    #     # PV generation
    #     model += PV_kw[t] == PV_adjustment*p_df_all[location][t]
    #     #model += load[t]== p_df_all['Load'][t]
        
    #     # Pflow is the energy flow reuired *from the battery* to meet the load
    #     # Negative if load greater than PV, positive if PV greater than load
    #     model += delta[t] == PV_kw[t] - p_df_all['Load'][t]
        
    #     # Given the below, it will push Pflow available for charge to zero or to to or greater than excess PV
    #     model += charging[t] >= 0
    #     model += charging[t] >= delta[t]

    #     # If Pflow is negative (discharge), then it will at least ePflowual discharge rePflowuired
    #     # If Pflow is positive (charge), then Pdischarge (discharge rePflowuired will ePflowual 0)
    #     model += discharging[t] <= 0
    #     model += discharging[t] <= delta[t]
    #     # Discharge cannot exceed available charge in battery
    #     # Discharge is negative

    #     model += PV_kw[t] - charging[t] + discharging[t] == p_df_all['Load'][t]
    #     # Ensures that energy flow required is satisifed by charge and discharge flows
    #     model += delta[t] == charging[t] + discharging[t]
    #     model += discharging[t] >= (-1)*BatteryLevel[t-1]
        
    #     model += charging_a[t] <= battery_hours*power - BatteryLevel[t-1]
        
    #     # Limit amount charge delivered by the available space in the battery
    #     model += charging_a[t] >= 0
    #     model += charging_a[t] <= charging[t]

    #     model += BatteryLevel[t] >= 0
    #     model += BatteryLevel[t] <= battery_hours*power

    # # for n in N:
    # #     model += sum(switch[n,m] for m in M) <= 1
    # L = -10000
    # U = 10000
    # u = 20000
    # #discharge_index =[k for k in modes.keys() if k == 'Discharging']
    # #charge_index =[k for k in modes.keys() if k == 'Charging']
    # model += (BatteryLevel[0]) == battery_hours*power
    # for i in p_df_all.index:
    #     try:
    #         #The issue is the case when the difference is below zero switch should be 1 for Discharge and 0 for Charge
    #         model += delta[i+1] == (PV_adjustment*p_df_all[location][i+1]-p_df_all['Load'][i+1])

    #         # model += delta[i+1]<=chargeswitch[i+1]*U
    #         # model += delta[i+1]>=(1-chargeswitch[i+1])*U

    #         # # model += L<=delta[i+1]<=U
    #         # # #Turns the chargeswitch to 1 when delta i >=0
    #         # # model += U*chargeswitch[i+1] - delta[i+1]>=0
    #         # # model += -L*(1-chargeswitch[i+1])+ delta[i+1]>=0

    #         # # #Turns the dischargeswitch to 1 when delta i <0
    #         # # model += U*(1-dischargeswitch[i+1]) - delta[i+1]>=0
    #         # # model += -L*dischargeswitch[i+1]+ delta[i+1]>=0

    #         # #handle the switch*delta product
    #         # model += y1[i+1]<=chargeswitch[i+1]*u
    #         # model += y1[i+1]<=delta[i+1]
    #         # model += y1[i+1]>=delta[i+1]-u*(1-chargeswitch[i+1])
    #         # model += y1[i+1]>=0

    #         # model += y2[i+1]<=dischargeswitch[i+1]*u
    #         # model += y2[i+1]<=delta[i+1]
    #         # model += y2[i+1]>=delta[i+1]-u*(1-dischargeswitch[i+1])
    #         # model += y2[i+1]>=0

    #         #Model of PV
    #         #model += PVload[i+1] == chargeswitch[i+1]*p_df_all['Load'][i+1] #power to load
    #         #model += charging[i+1] == y1[i+1]*efficiency_charge
    #         #model += discharging[i+1] ==y2[i+1]*efficiency_discharge
    #         #model += PV_adjustment*p_df_all[location][i+1] + discharging[i+1]== p_df_all['Load'][i+1]

    #         model += charging[i+1]>=0
    #         model += delta[i+1]<=charging[i+1]

    #         model += discharging[i+1]<=0
    #         model += delta[i+1]>=discharging[i+1]
    #         model += delta[i+1] == discharging[i+1] + charging[i+1]
    #         model += discharging[i+1]>=(-1)*BatteryLevel[i]
            
    #         model += BatteryLevel[i+1] >=0
    #         model += BatteryLevel[i+1] == BatteryLevel[i] + charging_a[i+1] + discharging[i]
    #         model += charging_a[i+1]>=0
    #         model += charging_a[i+1] <= charging[i+1]
    #         model += charging_a[i+1] <= battery_hours*power - BatteryLevel[i]

    #         #model += PV_adjustment*p_df_all[location][i] + charging[i] + discharging[i]>=0

    #         #model += balancingovershoot[i+1]>=0
    #         #model += BatteryLevel[i] <=battery_hours*power

    #     except:
    #         print('End of file')
    #         print(i)
    #         break

    # model.solve()
    # for v in model.variables():

    #     print(v.name, "=", v.varValue)
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

