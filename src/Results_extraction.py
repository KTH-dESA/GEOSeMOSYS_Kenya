import geopandas as gpd
import pandas as pd
import numpy as np
from sklearn.mixture import GaussianMixture
from sklearn.cluster import KMeans


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
        dict_results[c] = subdf
        subdf.to_csv(data +c+'.csv')

    return dict_results

def normalize(data):
    minima = np.min(data, axis=0)
    maxima = np.max(data, axis=0)
    a = 1 / (maxima - minima)
    b = minima / (minima - maxima)
    data = a * data + b
    return data

#number of clusters + data
def clustering(n_clusters, data, xstring, ystring, zstring, wstring): #, vstring, kstring,gstring,mstring,hstring

    #kmeans = KMeans(n_clusters=n_clusters, random_state=0).fit_predict(data)

    gm = GaussianMixture(n_components=n_clusters, random_state=0)
    gm.fit(data)
    #pred = kmeans.fit(data)
    pred = gm.predict(data)

    x = []
    y = []
    z = []
    w = []
    v = []
    k = []
    g = []
    m = []
    h = []
    for i in range(0, len(data)):
        x.append(data[i][0])
        y.append(data[i][1])
        z.append(data[i][2])
        w.append(data[i][3])
        #v.append(data[i][4])
       # k.append(data[i][5])
       # g.append(data[i][6])
       # m.append(data[i][7])
       # h.append(data[i][8])

    df = pd.DataFrame()
    df[xstring] = x
    df[ystring] = y
    df[zstring] = z
    df[wstring] = w
    #df[vstring] = v
    #df[kstring] = k
    #df[gstring] = g
    #df[mstring] = m
    #df[hstring]=h
    df['class'] = pred

    return df

