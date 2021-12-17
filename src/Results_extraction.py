import geopandas as gpd
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans


def read_data(data):
    """
    Creates a dictionary of param in results text file and returns it
    :param data:
    :return:
    """
    col =['param','region','tech','f','2016','2017','2018','2019','2020','2021','2022','2023','2024','2025','2026','2027','2028','2029','2030','2031','2032','2033','2034','2035','2036','2037','2038','2039','2040','2041']
    df = pd.read_csv(data, sep='\t', names=col)
    param = df.param.unique()
    dict_results = {}

    for c in param:
        subdf = df.loc[df['param']==c]
        dict_results[c] = subdf
        subdf.to_csv('results/'+c+'.csv')

    return dict_results

def normalize(data):
    minima = np.min(data, axis=0)
    maxima = np.max(data, axis=0)
    a = 1 / (maxima - minima)
    b = minima / (minima - maxima)
    data = a * data + b
    return data

#number of clusters + data
def clustering(n_clusters, data, xstring, ystring):
    #normalize?
    #data_norm = normalize(data)
    kmeans = KMeans(n_clusters, random_state=0)
    kmeans.fit(data)
    pred = kmeans.predict(data) + 1

    x = []
    y = []
    for i in range(0, len(data)):
        x.append(data[i][0])
        y.append(data[i][1])

    df = pd.DataFrame()
    df[xstring] = x
    df[ystring] = y
    df['class'] = pred

    return df

read_data('results/REF_111221_solved.txt')