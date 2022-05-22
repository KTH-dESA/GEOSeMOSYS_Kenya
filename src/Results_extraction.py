import pandas as pd

def read_data(data):
    """
    Creates a dictionary of param in results text file and returns it
    :param data:
    :return:
    """
    col =['param','region','tech','f','2016','2017','2018','2019','2020','2021','2022','2023','2024','2025','2026','2027','2028','2029','2030','2031','2032','2033','2034','2035','2036','2037','2038','2039','2040','2041']
    df = pd.read_csv(data, sep='\s+', names=col)
    param = df.param.unique()
    dict_results = {}

    for c in param:
        subdf = df.loc[df['param']==c]
        cols = ['2016','2017','2018','2019','2020','2021','2022','2023','2024','2025','2026','2027','2028','2029','2030','2031','2032','2033','2034','2035','2036','2037','2038','2039','2040','2041']
        subdf['sumall'] = df[cols].sum(axis=1)
        subdf.drop(subdf.loc[subdf.sumall==0].index, inplace=True)
        dict_results[c] = subdf
        subdf.to_csv(data +c+'.csv')

    return dict_results


def resultscalculations(results, inputfile):
    """

    :param results:
    :param inputfile:
    :return:
    """

    #https://github.com/OSeMOSYS/otoole/blob/master/src/otoole/results/result_package.py
    def production_by_technology(df):
        """Compute production by technology

        ProductionByTechnology

        Notes
        -----
        From the formulation::

            r~REGION, l~TIMESLICE, t~TECHNOLOGY, f~FUEL, y~YEAR,
            sum{m in MODE_OF_OPERATION: OutputActivityRatio[r,t,f,m,y] <> 0}
                RateOfActivity[r,l,t,m,y] * OutputActivityRatio[r,t,f,m,y]
                * YearSplit[l,y] ~VALUE;
        """
        df['rater_yearsplit'] = df['2016'].multiply(df["value_x"], axis="index")
        df['ProductionbyTechnology'] = df['rater_yearsplit'] * df['value_y']

        return df
    #https://github.com/OSeMOSYS/otoole/blob/master/src/otoole/results/result_package.py
    def production_by_technology_annual(production_by_technology_df):
        """Aggregates production by technology to the annual level
        """
        try:
            production_by_technology = production_by_technology_df.copy(deep=True)
        except:
            print('Error in ProductionbyTechnology')



    def use_by_technology(self) -> pd.DataFrame:
        """UseByTechnology

        Notes
        -----
        From the formulation::

            r~REGION, l~TIMESLICE, t~TECHNOLOGY, f~FUEL, y~YEAR,
            sum{m in MODE_OF_OPERATION}
                RateOfActivity[r,l,t,m,y]
                * InputActivityRatio[r,t,f,m,y]
                * YearSplit[l,y]~VALUE;

        """
        try:
            rate_of_use = self["RateOfUseByTechnologyByMode"]
            year_split = self["YearSplit"]
        except KeyError as ex:
            raise KeyError(self._msg("UseByTechnology", str(ex)))

        data = rate_of_use.mul(year_split, fill_value=0.0)

        if not data.empty:
            data = data.groupby(
                ["REGION", "TIMESLICE", "TECHNOLOGY", "FUEL", "YEAR"]
            ).sum()

        return data[(data != 0).all(1)]

    #Read datafile to get outputactivity and yearsplit (from preprocessing script https://github.com/OSeMOSYS/OSeMOSYS_GNU_MathProg/blob/master/scripts/preprocess_data.py

    lines = []

    parsing = False
    parsing_year = False
    year_list = []
    yearsplit = []
    output_table = []

    params_to_check = ['OutputActivityRatio', 'YearSplit']

    with open(inputfile, 'r') as f:
        for line in f:
            if parsing_year:
                year_list += [line.strip()] if line.strip() not in ['', ';'] else []

            if line.startswith('set YEAR'):
                if len(line.split('=')[1]) > 1:
                    year_list = line.split()[3:-1]
                else:
                    parsing_year = True

            if line.startswith(";"):
                parsing_year = False

    start_year = year_list[0]

    with open(inputfile, 'r') as f:
        for line in f:
            details = line.split()
            if line.startswith(";"):
                parsing = False
            if parsing:
                if len(details) > 1:
                    if param_current == 'OutputActivityRatio':
                        tech = details[1].strip()
                        fuel = details[2].strip()
                        mode = details[3].strip()
                        year = details[4].strip()
                        value = details[5].strip()

                        if float(value) != 0.0:
                            output_table.append(tuple([tech, fuel, mode, year, value]))

                    if param_current == 'YearSplit':
                        ts = details[0].strip()
                        year = details[1].strip()
                        value = details[2].strip()
                        if float(value) != 0.0:
                            yearsplit.append(tuple([ts, year, value]))

            if any(param in line for param in params_to_check):
                param_current = details[1]
                parsing = True

    df_yearsplit = pd.DataFrame(yearsplit, columns=['TS','Year','value'])
    df_yearsplit.index = df_yearsplit.TS
    df_yearsplit = df_yearsplit[~df_yearsplit.index.duplicated()]
    df_yearsplit.drop('TS', inplace=True, axis=1)
    df_yearsplit.drop('2016', inplace=True, axis=0)
    df_output = pd.DataFrame(output_table,columns=['tech', 'fuel', 'mode', 'Year', 'value'])
    #df_output.index = df_output.tech
    rateofactivity = results['RateOfActivity']
    #header = rateofactivity.tech
    #new_header = [x.replace('&apos;', '') for x in header]
    #rateofactivity.tech = new_header
    #rateofactivity.index = new_header

    rate_yearsplit = pd.merge(rateofactivity, df_yearsplit, on='TS', how='inner')
    rate_yearsplit_output = pd.merge(rate_yearsplit, df_output, on='tech', how='inner')

    production_bytech = production_by_technology(rate_yearsplit_output)
    production_annual = production_by_technology_annual(production_bytech)

    production_annual.to_csv('run -reduced TS/results_ref/ProductionByTechnologyAnnual.csv')
