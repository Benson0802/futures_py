import numpy as np
from sklearn.cluster import KMeans
import pandas as pd
import math

def detect_level_method(df):
    '''
    取得支撐壓力的方法
    '''
    # df = pd.read_csv('data/60Min.csv').tail(500)
    # df['datetime'] = pd.to_datetime(df['datetime'])
    # df.set_index(['datetime'], inplace=True)
    close = np.array(df["close"])
    
    K = 6
    levels = []
    min_max_values = [[np.inf, -np.inf] for _ in range(K)]  # 初始化 min_max_values

    kmeans = KMeans(n_clusters=6).fit(df.values.reshape(-1, 1))
    clusters = kmeans.predict(df.values.reshape(-1, 1))[:len(df)]

    # Get min/max for each cluster
    for i in range(len(close)):
        # Get cluster assigned to price
        cluster = clusters[i]
        # Compare for min value
        if close[i] < min_max_values[cluster][0]:
            min_max_values[cluster][0] = close[i]
        # Compare for max value
        if close[i] > min_max_values[cluster][1]:
            min_max_values[cluster][1] = close[i]

    # Create container for combined values
    output = []
    # Sort based on cluster minimum
    s = sorted(min_max_values, key=lambda x: x[0])
    # For each cluster get average of
    for i, (_min, _max) in enumerate(s):
        # Append min from first cluster
        if i == 0:
            output.append(_min)
        # Append max from last cluster
        if i == len(min_max_values) - 1:
            output.append(_max)
        # Append average from cluster and adjacent for all others
        else:
            output.append(sum([_max, s[i+1][0]]) / 2)

    for cluster_avg in output:
        levels.append(math.ceil(cluster_avg))
    
    return levels