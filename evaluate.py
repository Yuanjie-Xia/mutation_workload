import scipy.cluster.hierarchy as spc
import sklearn.metrics as sm
import numpy as np
from scipy import stats, spatial
import pandas as pd
from statistics import stdev
from scipy.stats import pearsonr


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


def measure_s(signature, perf):
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
    signature['pvalue'] = 0
    signature['size'] = 1

    # Calculate stability value for time period in large cluster
    large_cluster_array = large_cluster['cluster'].to_numpy()
    for cluster in large_cluster_array:
        cluster_time_period = signature.loc[lambda df: df['cluster'] == cluster]
        cluster_time_period = cluster_time_period['time_period'].to_numpy()
        first_sample = []
        for i in range(0, len(cluster_time_period) - 1):
            perf_data = perf.loc[lambda df: df['time_period'] == cluster_time_period[i]]
            cpu_data = perf_data['rss'].to_numpy()
            first_sample.extend(cpu_data)
            second_sample = first_sample.copy()
            perf_data = perf.loc[lambda df: df['time_period'] == cluster_time_period[i + 1]]
            cpu_data = perf_data['rss'].to_numpy()
            second_sample.extend(cpu_data)
            p_value = stats.ks_2samp(first_sample, second_sample)[1]
            if p_value >= 0.05:
                break
        signature['pvalue'] = np.where((signature['cluster'] == cluster), p_value, signature['pvalue'])
        signature['size'] = np.where((signature['cluster'] == cluster), len(cluster_time_period), signature['size'])
    #print(signature[['time_period', 'stability']])
    signature['stability'] = signature['pvalue'].rank(pct=True) * signature['size'].rank(pct=True)
    signature['stability'] = 1 - signature['stability'].rank(pct=True)
    signature.loc[signature['size'] == 1, 'stability'] = 1
    return signature


def measure_d(workload_store, url_workload, loop_time):
    workload = url_workload.copy()

    corr_max = []
    workload_store = workload.copy()
    workload_store['x1'] = 0
    if len(workload_store) > 0:
        for i in range(0, len(url_workload)):
            corr = []
            for k in range(0, len(workload_store)):
                # distance = 1 - spatial.distance.cosine(workload_store[k:k + 1], workload[i:i + 1])
                p_corr, _ = pearsonr(np.array(workload_store[k:k + 1])[0], np.array(workload[i:i + 1])[0])
                distance = 1 - p_corr
                corr.append(distance)
        # standardized
        #    if max(corr) - min(corr) > 0:
        #        std_corr = (corr - np.mean(corr)) / stdev(corr)
        #        max_corr = max(std_corr)
        #    else:
        #        max_corr = 0
        #    corr_max.append(max_corr)
        # normalized
        # rm_d_corr = 1 - (corr_max - min(corr_max)) / (max(corr_max) - min(corr_max))
        # print(rm_d_corr)
        url_workload['diversity'] = corr

    if loop_time < 1:
        url_workload['diversity'] = 1
        workload_store = pd.DataFrame(workload, columns=list(workload.columns))
    else:
        workload_store = pd.concat([workload_store.reset_index(), workload.reset_index()])
        # workload_store = workload_store.drop(columns=['time_period'])

    return url_workload, workload_store
