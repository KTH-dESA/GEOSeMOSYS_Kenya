import pandas as pd
import os
from os import listdir
from os.path import isfile, join
from datetime import datetime

import logging

logger = logging.getLogger(__name__)

def load_csvs(paths):
    """Creates a dataframe dictionary from the csv files in /data : dict_df

    Arguments
    ---------
    param_file : paths
        Path to the data files (/data)
    """
    filepaths = [f for f in listdir(paths) if isfile(join(paths, f))]
    onlyfiles = [os.path.join(paths, f) for f in filepaths]
    dict_df = {}
    for files in onlyfiles:
    #validate that the files are csv. Else the read function will not work
        _, filename = os.path.split(files)
        name, ending = os.path.splitext(filename)
        if ending == '.csv':
            dict_df[name] = pd.read_csv(files, header=0)
        else:
            print('You have mixed file types in you directory, please make sure all are .csv type! {}'.format(files))

    return dict_df

def make_outputfile(param_file):
    """Creates a string from the template OSeMOSYS file

    Arguments
    ---------
    param_file : str
        Path to the parameter file
    """
    allLinesFromXy = ""
    with open(param_file, "r") as inputFile:
        allLinesFromXy = inputFile.read()
    outPutFile = allLinesFromXy
    return outPutFile

def functions_to_run(dict_df, outPutFile):
    """Runs all the functions for the different parameters

    Arguments
    ---------
    dict_df, outPutFile
        dict_df: is a dictionary which contains all the csv files as dataframes from load_csv. Key is the name of the csv file
        outPutFile: is a string with the empty OSeMOSYS parameters file from make_outputfile
    """
    if 'operational_life' in dict_df:
        outPutFile = operational_life(outPutFile, dict_df['input_data'], dict_df['operational_life'])
    else:
        print('No operational_life file')
#######################################################################
    if 'peakdemand' in dict_df:
        outPutFile = peakdemand(outPutFile, dict_df['input_data'], dict_df['peakdemand'])
    else:
        print('No peakdemand file')
#################################################################################
    if 'distributionlines' in dict_df:
        outPutFile = maxkm(outPutFile, dict_df['input_data'], dict_df['distributionlines'], dict_df['distribution'], dict_df['elec'])
    else:
        print('No distributionlines file')
########################################################################################################
    if 'capitalcostkm' in dict_df:
        outPutFile = capitalcostkmkW(outPutFile, dict_df['input_data'], dict_df['capitalcostkm'], dict_df['peakdemand'])

    else:
        print('No distributionlines file')
############################################################################################################

    if 'fixed_cost_vision' in dict_df:
        outPutFile = fixedcost(dict_df['GIS_data'], outPutFile, dict_df['input_data'], dict_df['fixed_cost_vision'])
    else:
        print('No fixed_cost file')
#####################################################################################
    if 'total_annual_technology_limit' in dict_df:
        outPutFile = totaltechnologyannualactivityupperlimit(dict_df['GIS_data'], outPutFile, dict_df['input_data'], dict_df['total_annual_technology_limit'])
    else:
        print('No total_annual_technology_limit file')
########################################################################################################
    if 'vision_demand' in dict_df:
        outPutFile = specifiedannualdemand(outPutFile, dict_df['vision_demand'], dict_df['input_data'])
    else:
        print('No demand file')
####################################################################################
    if 'capitalcost_RET_vision' in dict_df:
        outPutFile = capitalcost_dynamic(dict_df['GIS_data'], outPutFile, dict_df['capitalcost_RET_vision'],
                                        dict_df['capacityfactor_wind'], dict_df['capacityfactor_solar'],
                                        dict_df['input_data'],dict_df['elec'],dict_df['un_elec'], dict_df['battery'],dict_df['capacityfactor_solar_batteries_high'], dict_df['capacityfactor_solar_batteries_high'])
    else:
        print('No capitalcost_RET file')
###########################################################################
    if 'capitalcost' in dict_df:
        outPutFile = capitalcost(outPutFile, dict_df['capitalcost'], dict_df['input_data'])
    else:
        print('No capitalcost file')

# ################################################################################

    if 'capacitytoactivity' in dict_df:
        outPutFile = capacitytoactivity(dict_df['capacitytoactivity'], outPutFile, dict_df['input_data'])
    else:
        print('No capacitytoactivity file')
#################################################################################
    if 'demandprofile' in dict_df:
       outPutFile = SpecifiedDemandProfile(outPutFile, dict_df['demandprofile'], dict_df['demandprofile_rural'],
                                            dict_df['input_data'])
    else:
        print('No demandprofile file')
###########################################################
###################### Mode of operation parameters######################

    if 'emissions' in dict_df:
        outPutFile = emissionactivity(dict_df['GIS_data'], outPutFile, dict_df['input_data'], dict_df['emissions'])
    else:
        print('No emissions file')
########################################################
    if 'variable_cost' in dict_df:
        outPutFile = variblecost(dict_df['GIS_data'], outPutFile, dict_df['input_data'], dict_df['variable_cost'])
    else:
        print('No variable_cost file')
#############################################################
    if 'inputactivity' in dict_df:
        outPutFile = inputact(outPutFile, dict_df['inputactivity'], dict_df['input_data'])
    else:
        print('No inputactivity file')

################################################################
    if 'outputactivity' in dict_df:
        outPutFile = outputactivity(outPutFile, dict_df['outputactivity'], dict_df['input_data'])
    else:
        print('No outputactivity file')

    ################################################################

    if ('capacityfactor_solar' or 'capacityfactor_wind') in dict_df.keys():
       outPutFile = capacityfactor(outPutFile, dict_df['GIS_data'], dict_df['battery'], dict_df['input_data'],
                                  dict_df['capacityfactor_wind'], dict_df['capacityfactor_solar'], dict_df['elec'], dict_df['un_elec'])
    else:
       print('No capacityfactor_solar or capacityfactor_wind file')
    ###############################################################################

    return(outPutFile)

def operational_life(outPutFile, input_data, operational_life):
    """
    builds the OperationalLife (Region, Technology, OperationalLife)
    -------------
    Arguments
    outPutFile, GIS_data, input_data, operational_life
        outPutFile: is a string containing the OSeMOSYS parameters file
        GIS_data: is the location specific data which is used to iterate the data
        input_data: contains meta data such as region, start year, end year, months, timeslices
        OperationalLife: is the operational life per technology
    """
    dataToInsert = ""
    print("Operational life", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    param = "param OperationalLife default 1 :=\n"
    startIndex = outPutFile.index(param) + len(param)

    #for i, row in GIS_data.iterrows():
        #location = row['Location']
    for m, line in operational_life.iterrows():
        t = line['Technology']
        l = line['Life']
        dataToInsert += "%s\t%s\t%i\n" % (input_data['region'][0],t, l)
    outPutFile = outPutFile[:startIndex] + dataToInsert + outPutFile[startIndex:]

    return(outPutFile)

def peakdemand(outPutFile,input_data, peakdemand):
    dataToInsert = ""
    print("Peak demand", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    param = "param Peakdemand default 999999999:=\n"
    startIndex = outPutFile.index(param) + len(param)

    peakdemand.index = peakdemand['Fuel']
    demand = peakdemand.drop(columns=['Fuel'])
    for j, row in demand.iterrows():
        year = demand.columns
        for k in year: #year is an object so I cannot match it with a number (e.g. startyear)
            demandForThisYearAndlocation = demand.loc[j][k]
            dataToInsert += "%s\t%s\t%s\t%s\n" % (input_data['region'][0], j, k, round(demandForThisYearAndlocation,4))
    outPutFile = outPutFile[:startIndex] + dataToInsert + outPutFile[startIndex:]
    return(outPutFile)

def maxkm(outPutFile,input_data, distributionlines, distributioncelllength, elec):
    dataToInsert = ""
    print("Max km Distribution", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    param = "param MaxKmPerTech default 9999999999 :=\n"
    startIndex = outPutFile.index(param) + len(param)

    distributionlines = distributionlines.set_index(distributionlines.iloc[:, 0])
    distribution = distributionlines.drop(columns ='Unnamed: 0')

    distributioncelllength.index = distributioncelllength['pointid']
    distribtionlength = distributioncelllength.drop(['Unnamed: 0', 'pointid', 'elec'], axis = 1)

    distribution_total = distribution.multiply(distribtionlength.LV_km, axis = "rows")

    for j, row in distribution_total.iterrows():
        km = distribution_total.loc[j]['0']
        year = int(input_data['startyear'][0])
        while year <= int(input_data['endyear'][0]):
            dataToInsert += "%s\tTRLV_%i_0\t%i\t%f\n" % (input_data['region'][0],j, year, round(km,4))
            if elec['pointid'].eq(j).any():
                dataToInsert += "%s\tTRLVM_%i_0\t%i\t%f\n" % (input_data['region'][0], j, year, round(km,4))
            year += 1
    outPutFile = outPutFile[:startIndex] + dataToInsert + outPutFile[startIndex:]
    return(outPutFile)

def capitalcostkmkW(outPutFile,input_data, capitalcost_distributionlines, peakdemand):
    dataToInsert = ""
    print("Captialcost per km", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    param = "param CapitalCostkmkW default 0 :=\n"
    startIndex = outPutFile.index(param) + len(param)

    peakdemand.index = peakdemand['Fuel']
    demand = peakdemand.drop(columns=['Fuel'])
    for j, row in peakdemand.iterrows():
        year = demand.columns
        for k in year:
            dataToInsert += "%s\t%s\t%s\t%f\n" % (input_data['region'][0], j, k, capitalcost_distributionlines.loc[0]['LV_cost'])
    outPutFile = outPutFile[:startIndex] + dataToInsert + outPutFile[startIndex:]
    return(outPutFile)

def fixedcost(df, outPutFile, input_data, fixed_cost):
    """
    Builds the Fixed cost (Region, Technology, Year, Fixed cost)
    -------------
    Arguments
    df, outPutFile, input_data, fixed_cost
        outPutFile: is a string containing the OSeMOSYS parameters file
        df: is the location specific data which is used to iterate the data
        input_data: contains meta data such as region, start year, end year, months, timeslices
        fixed_cost: is the fixed cost per technology
    """
    print("Fixed cost", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    dataToInsert = ""
    param = "param FixedCost default 0 :=\n"
    startIndex = outPutFile.index(param) + len(param)

    #for i, row in df.iterrows():
       #location = row['Location']

    for m, line in fixed_cost.iterrows():
        t = line['Technology']
        fc = line['Fixed Cost']
        year = int(input_data['startyear'][0])
        while year <= int(input_data['endyear'][0]):
            dataToInsert += "%s\t%s\t%i\t%f\n" % (input_data['region'][0], t,year, fc)
            year += 1
    outPutFile = outPutFile[:startIndex] + dataToInsert + outPutFile[startIndex:]
    return(outPutFile)

def emissionactivity(df, outPutFile, input_data, emissions):
    """
    Builds the Emission activity (Region, Technology, Emissiontype, Technology, ModeofOperation, Year, emissionactivity)
    -------------
    Arguments
    df, outPutFile, input_data, emissions
        outPutFile: is a string containing the OSeMOSYS parameters file
        df: is the location specific data which is used to iterate the data
        input_data: contains meta data such as region, start year, end year, months, timeslices
        emissions: is the emissionactivity per technology and mode of operation
    """
    print("Emission activity", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    dataToInsert = ""
    param = "param EmissionActivityRatio default 0 :=\n"
    startIndex = outPutFile.index(param) + len(param)
    for i, row in df.iterrows():
       location = row['Location']
       for m, line in emissions.iterrows():
           year = int(input_data['startyear'][0])
           t = line['Technology']
           k = line['Modeofoperation']
           CO2 = line['CO2']
           NOx = line['NOx']
           while year <=  int(input_data['endyear'][0]):
               dataToInsert += "%s\t%s_%i\tCO2\t%i\t%i\t%f\n" % (input_data['region'][0], t, location, k, year, CO2)
               dataToInsert += "%s\t%s_%i\tNOX\t%i\t%i\t%f\n" % (input_data['region'][0], t, location, k, year, NOx)
               year += 1
    outPutFile = outPutFile[:startIndex] + dataToInsert + outPutFile[startIndex:]
    return (outPutFile)

def variblecost(df, outPutFile, input_data, variable_cost):
    """
    Builds the Variable cost (Region, Technology, ModeofOperation, Year, Variablecost)
    -------------
    Arguments
    df, outPutFile, input_data, variable_cost
        outPutFile: is a string containing the OSeMOSYS parameters file
        df: is the location specific data which is used to iterate the data
        input_data: contains meta data such as region, start year, end year, months, timeslices
        variable_cost: is the variable cost per technology and mode of operation
    """

    print("Variable cost", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    dataToInsert = ""
    param = "param VariableCost default 0 :=\n"
    startIndex = outPutFile.index(param) + len(param)


    for m,line in variable_cost.iterrows():
        year = int(input_data['startyear'][0])
        while year <= int(input_data['endyear'][0]):
            t = line['Technology']
            vc = line['Variable Cost']
            modeofop = line['ModeofOperation']
            dataToInsert += "%s\t%s\t%i\t%i\t%f\n" % (input_data['region'][0], t, modeofop, year, vc)
            year += 1

    outPutFile = outPutFile[:startIndex] + dataToInsert + outPutFile[startIndex:]
    return(outPutFile)

def totaltechnologyannualactivityupperlimit(df,outPutFile, input_data, totalannuallimit):
    """
    Builds the TotalTechnologyAnnualActivityUpperLimit (Region, Technology, Year, TotalTechnologyUpperLimit)
    -------------
    Arguments
    df,outPutFile, input_data, totalannuallimit
        outPutFile: is a string containing the OSeMOSYS parameters file
        df: is the location specific data which is used to iterate for the location specific the data
        input_data: contains meta data such as region, start year, end year, months, timeslices
        totalannuallimit: is the total annual limit per technology
    """

    print("TotalTechnologyAnnualActivityUpperLimit", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    dataToInsert = ""
    param = "param TotalTechnologyAnnualActivityUpperLimit default 99999999999 :=\n"
    startIndex = outPutFile.index(param) + len(param)

    for index, row in df.iterrows():
       location = row['Location']
       year = int(input_data['startyear'][0])
       while year <= int(input_data['endyear'][0]):
           for m, line in totalannuallimit.iterrows():
               tech = line['Technology']
               cf = line[location]
               dataToInsert += "%s\t%s_%i\t%i\t%f\n" % (input_data['region'][0], tech, location, year, cf)
           year = year + 1
    outPutFile = outPutFile[:startIndex] + dataToInsert + outPutFile[startIndex:]
    return(outPutFile)

def inputact(outPutFile, inputactivity, input_data):
    """
    Builds the InputactivityRatio (Region, Technology, Fuel, Modeofoperation, Year, InputactivityRatio)
    -------------
    Arguments
    outPutFile, inputactivity, input_data
        outPutFile: is a string containing the OSeMOSYS parameters file
        input_data: contains meta data such as region, start year, end year, months, timeslices
        inputactivity: is the inputactivity per fuel and technology
    """
    dataToInsert = ""
    print("Input activity", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    param = "param InputActivityRatio default 0 :=\n"
    startIndex = outPutFile.index(param) + len(param)

    for j, row in inputactivity.iterrows():
       technology = row['Technology']
       fuel = row['Fuel']
       inputactivityratio = row['Inputactivity']
       modeofoperation = row['ModeofOperation']
       year = int(input_data['startyear'][0])
       dataToInsert += "\n[%s,%s,%s,*,*]:\n" % (
       input_data['region'][0], technology, fuel)
       while year<=int(input_data['endyear'][0]):
           dataToInsert += "%i\t" % (year)
           year = year + 1

       year = int(input_data['startyear'][0])
       dataToInsert += ":=\n%i\t" % (modeofoperation)
       while year <= int(input_data['endyear'][0]):
           dataToInsert += "%f\t" % (inputactivityratio)

           year = year + 1
    outPutFile = outPutFile[:startIndex] + dataToInsert + outPutFile[startIndex:]
    return (outPutFile)

def SpecifiedDemandProfile(outPutFile, demandprofile, demandprofile_rural, input_data):
    """
    Builds the SpecifiedDemandProfile (Region, Fuel, Timeslice, Year, SpecifiedDemandProfile)
    -------------
    Arguments
    outPutFile, demandprofile,input_data
        outPutFile: is a string containing the OSeMOSYS parameters file
        input_data: contains meta data such as region, start year, end year, months, timeslices
        demandprofile: is the demandprofile per fuel and technology
    """
    dataToInsert = ""
    print("SpecifiedDemandProfile", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    param = "param SpecifiedDemandProfile default 0 :=\n"
    startIndex = outPutFile.index(param) + len(param)

    fuels = input_data['Demand fuel']
    demand_fuels = [x for x in fuels if str(x) != 'nan']
    d = demandprofile.columns[1:]
    dr = demandprofile_rural.columns[1:]
    demandprofile.index = demandprofile['Timeslice']
    demandprofile_rural.index = demandprofile_rural['Timeslice']
    for i in demand_fuels:
        start, mid, end = i.split('_')
        if end == '1':
            for k, line in demandprofile.iterrows():
                timeslice = line['Timeslice']
                for j in d:
                    demand_value = demandprofile.loc[timeslice][j]
                    dataToInsert += "%s\t%s\t%s\t%s\t%f\n" % (input_data['region'][0], i, timeslice, j, round(demand_value,4))
        else:
            for k, line in demandprofile_rural.iterrows():
                timeslice = line['Timeslice']
                for j in dr:
                    value = demandprofile_rural.loc[timeslice][j]
                    dataToInsert += "%s\t%s\t%s\t%s\t%f\n" % (input_data['region'][0], i, timeslice, j, round(value,4))
    outPutFile = outPutFile[:startIndex] + dataToInsert + outPutFile[startIndex:]
    return(outPutFile)

def capacityfactor(outPutFile, df, battery, input_data, capacityfactor_wind, capacityfactor_solar, elec, un_elec):
    """
    builds the Capacityfactor(Region, Technolgy, Timeslice, Year, CapacityFactor)
    This method is for capacityfactor which does not use storage equations but still model batteries
    -------------
    Arguments
    outPutFile, df, capacityfactor_solar, input_data, capitalcost_RET
        outPutFile: is a string containing the OSeMOSYS parameters file
        df: is the location specific data which is used to iterate the data
        battery: contains meta data on technologies that you want ot model batteries, time and capacityfactor
        input_data: contains meta data such as region, start year, end year, months, timeslices
        capitalcost_RET: --
    """
    print("Capacity factor", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    param = "param CapacityFactor default 1 :=\n"
    startIndex = outPutFile.index(param) + len(param)
    dataToInsert = ""

    #read input data
    def convert(value):
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value
    # month = (input_data['Month']) #the list includes Nan
    # mon = [convert(value) for value in month]
    # mont = [x for x in mon if str(x) != 'nan']
    # months = ['{:02d}'.format(x) for x in mont] #padding numbers
    timeslice_ = input_data['Timeslice']
    timeslice = [x for x in timeslice_ if str(x) != 'nan']

    timeslicemonthstart_ = input_data['Timeslicemonthstart']
    timeslicemonthstart_ = [convert(value) for value in timeslicemonthstart_]
    timeslicemonthstart = [x for x in timeslicemonthstart_ if str(x) != 'nan']
    #timeslicemonthstart = ['{:02d}'.format(x) for x in timeslicemonthstart]

    timeslicemonthend_ = input_data['Timeslicemonthend']
    timeslicemonthend_ = [convert(value) for value in timeslicemonthend_]
    timeslicemonthend = [x for x in timeslicemonthend_ if str(x) != 'nan']
    #timeslicemonthend = ['{:02d}'.format(x) for x in timeslicemonthend]

    daysplit_ = input_data['Daysplit']
    daysplit = [x for x in daysplit_ if str(x) != 'nan']

    daysplitstart_ = input_data['Daysplitstart']
    daysplitstart = [x for x in daysplitstart_ if str(x) != 'nan']

    daysplitend_ = input_data['Daysplitend']
    daysplitend = [x for x in daysplitend_ if str(x) != 'nan']

    region = input_data['region'][0]
    startyear = input_data['startyear'][0]
    endyear = input_data['endyear'][0]
    type = input_data.groupby('renewable ninjafile')
    solar = type.get_group('capacityfactor_solar')
    solar_tech = solar['Tech']
    wind = type.get_group('capacityfactor_wind')
    wind_tech = wind['Tech']

    #deep copy renewable ninja data
    capacityfactor_solar_ = capacityfactor_solar.copy()
    capacityfactor_solar_p = pd.to_datetime(capacityfactor_solar_['adjtime'], errors='coerce', format='%Y/%m/%d %H:%M')
    capacityfactor_solar_.index = capacityfactor_solar_p
    capacityfactor_solar_pv = capacityfactor_solar_.drop(columns=['adjtime'])

    def calculate_average(data, startdate, enddate, sliceStart, sliceEnd, location):
        mask = (data.index > startdate) & (data.index <= enddate)
        thisMonthOnly = data.loc[mask]
        slice = sum(thisMonthOnly[(location)].between_time(sliceStart, sliceEnd))
        try:
            average = ((slice / len(thisMonthOnly.between_time(sliceStart, sliceEnd))))
        except ZeroDivisionError:
            average = 0
        return (average)

    #SolarPV
    for k, row in df.iterrows():
        location = str(row['Location'])
        year = startyear
        while year <= endyear:
            m = 0
            while m < len(timeslice):
                startDate = pd.to_datetime("2016-%s" % (timeslicemonthstart[m]))
                endDate = pd.to_datetime("2016-%s" % (timeslicemonthend[m]))
                average_solar_day = calculate_average(capacityfactor_solar_pv, startDate, endDate, daysplitstart[0], daysplitend[0], location)
                tsday = timeslice[m] + "_" + daysplit[0]
                average_solar_evening = calculate_average(capacityfactor_solar_pv, startDate, endDate, daysplitstart[1], daysplitend[1], location)
                tsevening = timeslice[m] + "_" + daysplit[1]
                average_solar_night = calculate_average(capacityfactor_solar_pv, startDate, endDate, daysplitstart[2], daysplitend[2], location)
                tsnight = timeslice[m] + "_" + daysplit[2]
                for t in solar_tech:
                    if t == 'SOPV':
                        if elec['pointid'].eq(row['Location']).any():
                            dataToInsert += "%s\t%s_%s_1\t%s\t%i\t%f\n" % (region, t, location, tsday, year, round(average_solar_day,4))
                            dataToInsert += "%s\t%s_%s_0\t%s\t%i\t%f\n" % (region, t, location, tsday, year, round(average_solar_day,4))
                            dataToInsert += "%s\t%s_%s_1\t%s\t%i\t%f\n" % (region, t, location, tsevening, year, round(average_solar_evening,4))
                            dataToInsert += "%s\t%s_%s_0\t%s\t%i\t%f\n" % (region, t, location, tsevening, year, round(average_solar_evening,4))
                            dataToInsert += "%s\t%s_%s_1\t%s\t%i\t%f\n" % (region, t, location, tsnight, year, round(average_solar_night,4))
                            dataToInsert += "%s\t%s_%s_0\t%s\t%i\t%f\n" % (region, t, location, tsnight, year, round(average_solar_night,4))
                        if un_elec['pointid'].eq(row['Location']).any():
                            dataToInsert += "%s\t%s_%s_0\t%s\t%i\t%f\n" % (region, t, location, tsday, year, round(average_solar_day,4))
                            dataToInsert += "%s\t%s_%s_0\t%s\t%i\t%f\n" % (region, t, location, tsevening, year, round(average_solar_evening,4))
                            dataToInsert += "%s\t%s_%s_0\t%s\t%i\t%f\n" % (region, t, location, tsnight, year, round(average_solar_night,4))
                    else:
                        dataToInsert += "%s\t%s_%s\t%s\t%i\t%f\n" % (region, t, location, tsday, year, round(average_solar_day,4))
                        dataToInsert += "%s\t%s_%s\t%s\t%i\t%f\n" % (region, t, location, tsevening, year, round(average_solar_evening,4))
                        dataToInsert += "%s\t%s_%s\t%s\t%i\t%f\n" % (region, t, location, tsnight, year, round(average_solar_night,4))
                m +=1
            year += 1

#WIND
    capacityfactor_windcop = capacityfactor_wind.copy()
    capacityfactor_windc = pd.to_datetime(capacityfactor_windcop['adjtime'], errors='coerce', format='%Y/%m/%d %H:%M')
    capacityfactor_windcop.index = capacityfactor_windc
    capacityfactor_windcopy = capacityfactor_windcop.drop(columns=['adjtime'])

    for k, row in df.iterrows():
        location = str(row['Location'])
        year = startyear
        while year <= endyear:
            m = 0
            while m < len(timeslice):
                startDate = pd.to_datetime("2016-%s" % (timeslicemonthstart[m]))
                endDate = pd.to_datetime("2016-%s" % (timeslicemonthend[m]))
                average_wind_day = calculate_average(capacityfactor_windcopy, startDate, endDate,
                                                      daysplitstart[0], daysplitend[0], location)
                tsday = timeslice[m] + "_" + daysplit[0]
                average_wind_evening = calculate_average(capacityfactor_windcopy, startDate, endDate,
                                                          daysplitstart[1], daysplitend[1], location)
                tsevening = timeslice[m] + "_" + daysplit[1]
                average_wind_night = calculate_average(capacityfactor_windcopy, startDate, endDate,
                                                        daysplitstart[2], daysplitend[2], location)
                tsnight = timeslice[m] + "_" + daysplit[2]

                for t in wind_tech:
                    dataToInsert += "%s\t%s_%s\t%s\t%i\t%f\n" % (region, t, location , tsday, year, round(average_wind_day,4))
                    dataToInsert += "%s\t%s_%s\t%s\t%i\t%f\n" % (region, t, location, tsevening, year, round(average_wind_evening,4))
                    dataToInsert += "%s\t%s_%s\t%s\t%i\t%f\n" % (region, t, location, tsnight, year, round(average_wind_night,4))
                m = m + 1
            year = year + 1


    outPutFile = outPutFile[:startIndex] + dataToInsert + outPutFile[startIndex:]
    return (outPutFile)


def outputactivity(outPutFile, outputactivity, input_data):
    """
    builds the Outputactivity(Region, Technology, Fuel, ModeofOperation, Year, outputactivity)
    -------------
    Arguments
    outPutFile, outputactivity, input_data
        outPutFile: is a string containing the OSeMOSYS parameters file
        outputactivity: The outputactivity between the Technology and Fuel
        input_data: contains meta data such as region, start year, end year, months, timeslices
    """
    dataToInsert = ""
    print("Outputactivity", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    param = "param OutputActivityRatio default 0 :=\n"
    startIndex = outPutFile.index(param) + len(param)

    for j, row in outputactivity.iterrows():
       technology = row['Technology']
       fuel = row['Fuel']
       outputactivityratio = row['Outputactivity']
       modeofoperation = row['ModeofOperation']
       year = int(input_data['startyear'][0])
       dataToInsert += "\n[%s,%s,%s,*,*]:\n" % (
       input_data['region'][0], technology, fuel)
       while year<=int(input_data['endyear'][0]):
           dataToInsert += "%i\t" % (year)
           year = year + 1

       year = int(input_data['startyear'][0])
       dataToInsert += ":=\n%i\t" % (modeofoperation)
       while year <= int(input_data['endyear'][0]):
           dataToInsert += "%f\t" % (outputactivityratio)

           year = year + 1

    outPutFile = outPutFile[:startIndex] + dataToInsert + outPutFile[startIndex:]
    return(outPutFile)

def specifiedannualdemand(outPutFile, demand, input_data):
    """
    builds the SpecifiedAnnualDemand (Region, Fuel, Year, Demand)
    -------------
    Arguments
    outPutFile, demand, input_data
        outPutFile: is a string containing the OSeMOSYS parameters file
        demand: The demand per Fuel
        input_data: contains meta data such as region, start year, end year, months, timeslices
    """
    print("SpecifiedAnnualDemand", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    param = "param SpecifiedAnnualDemand default 0 :=\n"
    dataToInsert = ""
    startIndex = outPutFile.index(param) + len(param)
    demand.index = demand['Fuel']
    demand = demand.drop(columns=['Fuel'])
    for j, row in demand.iterrows():
        year = demand.columns
        for k in year: #year is an object so I cannot match it with a number (e.g. startyear)
            demandForThisYearAndlocation = demand.loc[j][k]
            dataToInsert += "%s\t%s\t%s\t%f\n" % (input_data['region'][0], j, k, round(demandForThisYearAndlocation,4))
    outPutFile = outPutFile[:startIndex] + dataToInsert + outPutFile[startIndex:]
    return(outPutFile)

def capitalcost_dynamic(df, outPutFile, capitalcost_RET, capacityfactor_wind, capacityfactor_solar, input_data, elec, un_elec, battery, capacityfactor_solar_batteries_low, capacityfactor_solar_batteries_high):
    """
    builds the Capitalcost (Region, Technology, Year, CapitalCost) where the cost is dynamic. Here when the capacity factor vary for Wind
    -------------
    Arguments
    df, outPutFile, capitalcost_RET, capacityfactor_wind, capacityfactor_solar, input_data
        df: is the location specific data which is used to iterate the data
        outPutFile: is a string containing the OSeMOSYS parameters file
        capitalcost_RET: The capital cost per technology and capacity factor
        capacityfactor_wind: Hourly 8760 wind CF file for each location
        capacityfactor_solar: Hourly 8760 solar CF file for each location
        input_data: contains meta data such as region, start year, end year, months, timeslices
    """
    dataToInsert = ""
    print("Capital cost dynamic cost", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    param = "param CapitalCost default 0 :=\n"
    startIndex = outPutFile.index(param) + len(param)

    #Section the different technology types per CF and OSeMOSYS name
    cf_tech = capitalcost_RET.groupby('Technology')
    wind_tech = cf_tech.get_group('Wind')
    wind_CF = wind_tech['CF']
    wind_tech_name = wind_tech.loc[0]['Technology_name_OSeMOSYS']
    comm_PV_tech =  cf_tech.get_group('Comm PV')
    comm_PV_CF = comm_PV_tech['CF']
    comm_PV_tech_name = comm_PV_tech.loc[1]['Technology_name_OSeMOSYS']
    pv_tech = cf_tech.get_group('PV')
    pv_CF = pv_tech['CF']
    pv_tech_name = pv_tech.loc[2]['Technology_name_OSeMOSYS']
    battery_tech = cf_tech.get_group('Battery')
    battery_tech_name = battery_tech.loc[3:4]['Technology_name_OSeMOSYS']
    battery_CF = battery_tech['CF']
    battery_tech.index = battery_tech['CF']

    #Caluculate the CF for the location over the year
    for m, row in df.iterrows():
       location = str(row['Location']) # This is needed because the columns in capacityfactor_wind isn't int64. They are strings.
       slice_wind = sum(capacityfactor_wind[location])
       average_wind = (slice_wind / len(capacityfactor_wind._values))

       slice_solar = sum(capacityfactor_solar[location])
       average_solar = (slice_solar / len(capacityfactor_solar._values))

       # Wind
       for k in wind_tech.columns[3:]:  # year is an object so I cannot match it with a number (e.g. startyear)
          def find_nearest(wind_CF, average_wind):
              #arraywind = np.asarray(float(wind_CF))
              #idx = (np.abs(arraywind - average_wind)).argmin()
              return str(0.25)
          cf=find_nearest(wind_CF, average_wind)
          wind_tech.index = wind_tech['CF']
          windcapitalcost = wind_tech.loc[cf][k]
          dataToInsert += "%s\t%s_%s\t%s\t%f\n" % (input_data['region'][0], wind_tech_name, location, k, round(windcapitalcost,4))

       if battery_tech is None:
           pass
       else:
           for k in wind_tech.columns[3:]:  # year is an object so I cannot match it with a number (e.g. startyear)
               windcapitalcostbatt = wind_tech.loc[cf][k] + battery_tech.loc['4c'][k]
               techname = wind_tech_name + battery_tech_name.loc[4]
               #dataToInsert += ("%s\t%s_%s\t%s\t%f\n" % (input_data['region'][0], techname, location, k, windcapitalcostbatt))

       #Solar PV
       for k in pv_tech.columns[3:]: # year is an object so I cannot match it with a number (e.g. startyear)
          def find_nearest(pv_CF, average_solar):
             #arraysun = np.asarray(float(pv_CF))
             #idx = (np.abs(arraysun - average_solar)).argmin()
             return str(0.21)
          cf=find_nearest(pv_CF, average_solar)
          pv_tech.index = pv_tech['CF']
          pvcapitalcost = pv_tech.loc[cf][k]
          if elec['pointid'].eq(row['Location']).any():
            dataToInsert += ("%s\t%s_%s_1\t%s\t%f\n" % (input_data['region'][0], pv_tech_name, location, k, round(pvcapitalcost,4)))
            dataToInsert += (
                        "%s\t%s_%s_0\t%s\t%f\n" % (input_data['region'][0], pv_tech_name, location, k, round(pvcapitalcost,4)))
          if un_elec['pointid'].eq(row['Location']).any():
              dataToInsert += ("%s\t%s_%s_0\t%s\t%f\n" % (input_data['region'][0], pv_tech_name, location, k, round(pvcapitalcost,4)))
       if battery_tech is None:
            pass
       else:
        #Case elec = 0 low demand profile
           for k in pv_tech.columns[3:]:  # year is an object so I cannot match it with a number (e.g. startyear)
              sopvcapitalcostbatt = pv_tech.loc[cf][k]*capacityfactor_solar_batteries_low.loc[row['Location']]['PV_size']+ battery_tech.loc['res_kWh'][k]*capacityfactor_solar_batteries_low.loc[row['Location']]['Battery_hours']+ battery_tech.loc['res_constant'][k]
              techname = pv_tech_name+'8r'
              if elec['pointid'].eq(row['Location']).any():
                  dataToInsert += ("%s\t%s_%s_0\t%s\t%f\n" % (
                  input_data['region'][0], techname, location, k, sopvcapitalcostbatt))
              if un_elec['pointid'].eq(row['Location']).any():
                  dataToInsert += ("%s\t%s_%s_0\t%s\t%f\n" % (input_data['region'][0], techname, location, k, sopvcapitalcostbatt))
        #Case elec = 1 high demand profile
           for k in pv_tech.columns[3:]:  # year is an object so I cannot match it with a number (e.g. startyear)
              sopvcapitalcostbatt = pv_tech.loc[cf][k]*capacityfactor_solar_batteries_high.loc[row['Location']]['PV_size']+ battery_tech.loc['res_kWh'][k]*capacityfactor_solar_batteries_high.loc[row['Location']]['Battery_hours']+ battery_tech.loc['res_constant'][k]
              techname = pv_tech_name+'8r'
              if elec['pointid'].eq(row['Location']).any():
                  dataToInsert += ("%s\t%s_%s_1\t%s\t%f\n" % (input_data['region'][0], techname, location, k, sopvcapitalcostbatt))

       #Solar MG i excluded from the optimization
       for k in comm_PV_tech.columns[3:]:
          def find_nearest(comm_PV_CF, average_solar):
             #arraysun = np.asarray(comm_PV_CF)
             #idx = (np.abs(arraysun - average_solar)).argmin()
             return str(0.2)
          cf = find_nearest(comm_PV_CF, average_solar)
          comm_PV_tech.index = comm_PV_tech['CF']
          somgcapitalcost = comm_PV_tech.loc[cf][k]
       #    dataToInsert += ("%s\t%s_%s\t%s\t%f\n" % (input_data['region'][0], comm_PV_tech_name, location, k, somgcapitalcost))

       # Battery
       if battery_tech is None:
           pass
       else:
           for k in comm_PV_tech.columns[3:]:
               somgcapitalcostbatt = comm_PV_tech.loc[cf][k]*(capacityfactor_solar_batteries_high.loc[row['Location']]['PV_size']+capacityfactor_solar_batteries_low.loc[row['Location']]['PV_size'])/2 + battery_tech.loc['comm_kWh'][k]*(capacityfactor_solar_batteries_high.loc[row['Location']]['Battery_hours'] +capacityfactor_solar_batteries_low.loc[row['Location']]['Battery_hours'])/2 + battery_tech.loc['comm_constant'][k]
               techname = comm_PV_tech_name + '8c'
               dataToInsert += ("%s\t%s_%s\t%s\t%f\n" % (input_data['region'][0], techname, location, k, somgcapitalcostbatt))


    outPutFile = outPutFile[:startIndex] + dataToInsert + outPutFile[startIndex:]
    return(outPutFile)

def capitalcost(outPutFile, trade_cost, input_data):
    """
    builds the Capital cost (region,technology,year,capitalcost)
    -------------
    Arguments
    outPutFile, outputactivity, trade_cost
        outPutFile: is a string containing the OSeMOSYS parameters file
        trade_cost: The Capitalcost which is not dynamic
        input_data: contains meta data such as region, start year, end year, months, timeslices
    """
    dataToInsert = ""

    print("Capital cost", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    param = "param CapitalCost default 0 :=\n"
    startIndex = outPutFile.index(param) + len(param)

    for m, row in trade_cost.iterrows():
        if row['Technology'] != "":
            cost = row['Capitalcost']
            tech = row['Technology']
            year = int(input_data['startyear'][0])
            while year <= int(input_data['endyear'][0]):
                dataToInsert += "%s\t%s\t%i\t%f\n" % (input_data['region'][0], tech, year, round(cost,4))
                year += 1

    outPutFile = outPutFile[:startIndex] + dataToInsert + outPutFile[startIndex:]
    return(outPutFile)

def capacitytoactivity(trade, outPutFile, input_data):
    """
    builds the CapacityToActivityUnit (Region, Technology, CapacitytoActivityUnit)
    -------------
    Arguments
    trade, outPutFile, input_data
        outPutFile: is a string containing the OSeMOSYS parameters file
        trade: The capacitytoactivity for each technology
        input_data: contains meta data such as region, start year, end year, months, timeslices
    """
    dataToInsert = ""
    print("Capacity to activity", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    param = "param CapacityToActivityUnit default 1 :=\n"
    startIndex = outPutFile.index(param) + len(param)

    for m, row in trade.iterrows():
       capact = row['Capacitytoactivity']
       t = row['1']
       dataToInsert += "%s\t%s\t%f\n" % (input_data['region'][0],t ,capact)

    outPutFile = outPutFile[:startIndex] + dataToInsert + outPutFile[startIndex:]
    return(outPutFile)

def write_to_file(file_object, outPutFile):
    """
    write_to_file writes the string outPutFile to file_object
    -------------
    Arguments
    file_object, outPutFile
        file_object: is the path and name of the file where the datafile will be saved
        outPutFile:  is the accumulated final string of all data
    """
###############################################################
# write all to file
#########################################################
    print("write to file", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    with open(file_object, "w") as actualOutputFile:
       actualOutputFile.truncate(0) #empty the file
       actualOutputFile.write(outPutFile)
