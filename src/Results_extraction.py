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


