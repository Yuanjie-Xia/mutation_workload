import scipy.cluster.hierarchy as spc
import sklearn.metrics as sm
import numpy as np
from scipy import stats
import pandas as pd
from scipy.stats import pearsonr
import statistics


def hierarchical_clustering(signature):
    t_signature = signature.T
    corr = t_signature.corr().values
    distance = 1 - corr
    matrix_dist = spc.distance.pdist(distance)

    hierarchy_rank = spc.linkage(matrix_dist, method='complete')
    s_ch = 0
    best_cluster_num = 0
    for cluster_num in range(2, 4):
        cluster_result = spc.fcluster(hierarchy_rank, cluster_num, 'maxclust')
        ch = sm.calinski_harabasz_score(distance, cluster_result)
        if ch >= s_ch:
            s_ch = ch
            best_cluster_num = cluster_num

    cluster_result = spc.fcluster(hierarchy_rank, best_cluster_num, 'maxclust')
    signature['cluster'] = cluster_result
    return signature


def measure_s(signature, perf, config, model):
    # Get the size of the cluster
    cluster_amount = signature.copy()
    cluster_amount['count'] = cluster_amount.groupby('cluster')['cluster'].transform('count')
    cluster_amount = cluster_amount.drop_duplicates(['cluster'])
    cluster_amount = cluster_amount[['cluster', 'count']]
    cluster_amount = cluster_amount.sort_values(by=['cluster'])
    large_cluster = cluster_amount
    large_cluster = large_cluster.loc[lambda df: df['count'] > 1]

    # Generate stability value for time period in small cluster
    signature = signature.reset_index()
    # create training set
    series_input_train = signature.loc[:, signature.columns.str.startswith('x')].copy()
    series_input_train['cpulimit'] = config[0]
    series_input_train['memorylimit'] = config[1]
    series_input_train = np.expand_dims(series_input_train, axis=1)
    # create target part
    target = perf.loc[perf['time_period'] <= series_input_train.shape[0]]['cpu']
    target = np.expand_dims(target, axis=1)
    # cnn training model
    model.fit(series_input_train, target, batch_size=32, epochs=100)
    result = model.predict(series_input_train)
    signature['stability'] = 1 - abs(target - result)/target
    rate = 1 - statistics.median(signature['stability'])
    # print(signature[['time_period', 'stability']])
    signature['stability'] = signature['stability'].rank(pct=True)
    return signature, rate


def measure_d(workload_store, url_workload, config, loop_time):
    workload = url_workload.copy()
    corr_max = list()
    if len(workload_store) > 0:
        for i in range(0, len(url_workload)):
            workload['cpulimit'] = config[0]
            workload['memorylimit'] = config[1]
            corr = list()
            for k in range(0, min(len(workload), len(workload_store))):
                # distance = 1 - spatial.distance.cosine(workload_store[k:k + 1], workload[i:i + 1])
                print(np.array(workload_store[k:k + 1])[0])
                print(np.array(workload[i:i + 1])[0])
                p_corr, _ = pearsonr(np.array(workload_store[k:k + 1])[0], np.array(workload[i:i + 1])[0])
                distance = 1 - p_corr
                corr.append(distance)
            corr_max.append(max(corr))
        # standardized
        #    if max(corr) - min(corr) > 0:
        #        std_corr = (corr - np.mean(corr)) / stdev(corr)
        #        max_corr = max(std_corr)
        #    else:
        #        max_corr = 0
        #    corr_max.append(max_corr)
        # normalized
        #rm_d_corr = 1 - (corr_max - min(corr_max)) / (max(corr_max) - min(corr_max))
        # print(rm_d_corr)
        url_workload['diversity'] = corr_max
        url_workload['diversity'] = url_workload['diversity'].rank(pct=True)

    if loop_time < 1:
        url_workload['diversity'] = 0
        workload['cpulimit'] = config[0]
        workload['memorylimit'] = config[1]
        workload_store = workload
    else:
        # print(workload_store)
        # print(workload)
        workload_store = workload_store.append(workload)
        # workload_store = workload_store.drop(columns=['time_period'])
    url_workload = url_workload.reset_index()
    # print(url_workload)
    return url_workload, workload_store
