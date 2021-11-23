from time import time, ctime, localtime, sleep
import math
import random
import re
import os
import datetime
import pandas as pd
import scipy.cluster.hierarchy as spc
import sklearn.metrics as sm
import numpy as np
from scipy import stats,spatial
from statistics import stdev
import paramiko
from datetime import date, timedelta
import matplotlib.pyplot as plt
import threading

webServerIP = '10.128.0.31'
driveServerIP = '10.128.0.35'


# logFileAddress = '~/openmrs-core/webapp/target/access.log'
# perfFileAddress = '~/screenlog.0'


def transfer2type(action, url):
    url = str(url)
    #print(url)
    action = str(action)
    if re.search("encounter", url):
        if re.search("encountertype", url):
            url = "GET_URL4"
        else:
            url = "GET_URL5"

    if re.search("concept", url):
        url = "GET_URL6"

    if re.search("obs", url):
        url = "GET_URL7"

    if action == "POST":
        if url == "//10.128.0.45:8080/openmrs/ws/rest/v1/person":
            url = "POST_URL1"
        else:
            url = "POST_URL9"
            #print(url)

    if action == "DELETE":
        url = "DELETE_URL2"

    if re.search("person", url):
        if re.search("person\\?q=", url):
            url = "GET_URL3"
        else:
            url = "GET_URL8"

    return url


def load_file(log_address, perf_address, period_size,start_time):
    perf_data = open(perf_address, 'r')
    split_list = []
    i = 0

    for line in perf_data:
        if line.__contains__('openjdk'):
            #print(line)
            element_perf = line.split()
            while i == 0:
                start_time = int(element_perf[0])
                i = i + 1

            time_interval = int(element_perf[0]) - start_time
            time_period = math.floor(time_interval / (period_size * 3))+1
            time_round = math.floor(time_interval / (period_size))+1
            cpu = float(element_perf[6])
            rss = float(element_perf[11])
            memory = float(element_perf[12])
            if time_round%3==1:
               split_list.append([time_period, cpu, rss, memory])

    perf = pd.DataFrame(split_list, columns=['time_period', 'cpu', 'rss', 'memory'])
    #print(perf)
    log_data = open(log_address, 'r')
    #print(log_data)
    split_list = []
    normal_start_time = ctime(start_time)
    sp_start_time = normal_start_time.split()
    start_day = int(sp_start_time[2])
    start_hour = int(sp_start_time[3][0:2])
    start_minute = int(sp_start_time[3][3:5])
    start_second = int(sp_start_time[3][6:8])
    transfer_start_time = timedelta(days=start_day, hours=start_hour, minutes=start_minute,
                                             seconds=start_second)
    print('this loop start time:')
    print(transfer_start_time)
    for line in log_data:
        #print(line)
        elements = line.split()
        #print(len(elements))
        if len(elements)==14:
           day = int(elements[4][9:11])
           hour = int(elements[5][0:2])
           minute = int(elements[5][3:5])
           second = int(elements[5][6:8])
           current_time = timedelta(days=day, hours=hour, minutes=minute, seconds=second)
           #print(current_time)
           duration = (current_time - transfer_start_time).total_seconds()
           # Designed as the pidstat run after jmeter start
           time_period = math.floor(duration / (3 * period_size)) + 1
           #print(time_period)
           if time_period > 12:
               break
           if time_period < 1:
               continue
           action = elements[6][1:]
           url = elements[7]
           url = transfer2type(action, url)
           #print(url)
           response = elements[9]
           split_list.append([action, url, response, time_period])
        
    log = pd.DataFrame(split_list, columns=['action', 'url', 'respondCode', 'time_period'])
    search_value = ['POST', 'DELETE', 'GET']
    log = log.loc[log.url.str.contains('|'.join(search_value)), :]
    return log, perf


def generate_workload(abstracted_log):
    workload_count = abstracted_log.copy()
    abstracted_log['combine'] = abstracted_log['url'] + abstracted_log['respondCode'] + abstracted_log[
        'time_period'].astype(str)
    abstracted_log['combine1'] = abstracted_log['url'] + abstracted_log['respondCode']
    abstracted_log['n'] = abstracted_log.groupby("combine")['combine'].transform('count')
    abstracted_log = abstracted_log.drop_duplicates(['combine'])
    workload_signature = abstracted_log.pivot(index='time_period', columns='combine1', values='n').fillna(0)

    workload_count['combine'] = workload_count['url'] + workload_count['time_period'].astype(str)
    workload_count['n'] = workload_count.groupby("combine")['combine'].transform('count')
    workload_count = workload_count.drop_duplicates(['combine'])
    workload = workload_count.pivot(index='time_period', columns='url', values='n').fillna(0)

    return workload_signature, workload


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
    signature.loc[signature['size']==1,'stability'] = 1
    return signature



def robustCor(df, df1):
    df = df.to_numpy()
    df1 = df1.to_numpy()
    df = df[0]
    df1 = df1[0]
    #print(df)
    #print(df1)
    ave1 = np.mean(df)
    ave2 = np.mean(df1)
    std1 = stdev(df)
    std2 = stdev(df1)
    df = (df - ave1)/std1
    df1 = (df1 - ave2)/std2
    multidf = sum(df*df1)/(len(df)-1)
    return multidf



def measure_d(workload_store, signature, loop_time):
    workload = signature.copy()
    #workload = workload.drop(columns=['cluster'])
    workload = workload.reset_index()
    workload = workload[['DELETE_URL2', 'GET_URL3', 'GET_URL4', 'GET_URL5', 'GET_URL6', 'GET_URL7', 'GET_URL8', 'POST_URL9']]
    #workload_store = workload.copy()
    #workload_store['DELETE_URL2204'] = 0
    #print(workload_store)
    #workload_store = workload_store.replace({'DELETE_URL2204': {0: 100, 4: 400}})
    #print(workload_store['DELETE_URL2204'].iloc[[1,2]])
    maxcorr = []
    #print(np.corrcoef(workload_store, workload))
    if len(workload_store) > 0:
        workload_store = workload_store[['DELETE_URL2', 'GET_URL3', 'GET_URL4', 'GET_URL5', 'GET_URL6', 'GET_URL7', 'GET_URL8', 'POST_URL9']]
        for i in range(0, len(signature)):
            corr = []
            for k in range(0, len(workload_store)):
                distance = 1-spatial.distance.euclidean(workload_store[k:k+1], workload[i:i + 1])
                corr.append(distance)
            
            if max(corr)-min(corr) > 0:
                std_corr = (corr-np.mean(corr))/stdev(corr)
                max_corr = max(std_corr)
            else: max_corr = 0
            maxcorr.append(max_corr)
        
        rm_dimention_corr = 1 - (maxcorr - min(maxcorr))/(max(maxcorr)-min(maxcorr))
        #print(rm_dimention_corr)
        signature['diversity'] = rm_dimention_corr

    if loop_time < 1:
        signature['diversity'] = 1
        workload_store = pd.DataFrame(workload, columns=list(workload.columns))
    else:
        workload_store = pd.concat([workload_store.reset_index(), workload.reset_index()])
        #workload_store = workload_store.drop(columns=['time_period'])

    return signature, workload_store


def mutation(selected_workload):
    for i in range(0, np.size(selected_workload.columns)):
        v = random.randint(0, 1)
        if v == 1:
            line = selected_workload[selected_workload.columns[i]].to_numpy()
            temp = line[1]
            line[1] = line[0]
            line[0] = temp
            selected_workload[selected_workload.columns[i]] = line
    return selected_workload


def analysis_data(logFileAdd, perfFileAdd, workload_store, looptime):
    workload_signature, performance_data = load_file(logFileAdd, perfFileAdd, 30, 0)
    #print(workload_signature)
    #print(performance_data)
    performance_data.to_csv('~/performance/perf'+ str(looptime)  + '.csv', index=False)
    workload_signature, workload = generate_workload(workload_signature)
    #print(workload_signature)
    workload_signature = workload_signature[['DELETE_URL2204', 'GET_URL3200', 'GET_URL4200', 'GET_URL5200', 'GET_URL6200', 'GET_URL7200', 'GET_URL8200', 'POST_URL9200']]
    workload_signature = hierarchical_clustering(workload_signature)
    print('cluster detail:')
    print(workload_signature)
    workload_signature.to_csv('~/clusterData/clusterData' + str(looptime)  + '.csv', index=False)
    stability_value = measure_s(workload_signature, performance_data)
    #print(stability_value)
    diversity_value, workload_store = measure_d(workload_store, workload, looptime)
    diversity_value = diversity_value.reset_index()
    #print(diversity_value)
    stability_value['diversity'] = diversity_value['diversity'].to_numpy()
    stability_value['measurement'] = abs(stability_value['diversity']) + abs(stability_value['stability'])
    stability_value.to_csv('~/clusterData/rq' + str(looptime) + '.csv', index=False)
    print('rq detail:')
    print(stability_value)
    selection_df = stability_value.sort_values(by=['measurement'], ascending=False)
    selected_workload = selection_df[0:2]
    print(selected_workload)
    #selected_workload = selected_workload.reset_index()
    selected_time = selected_workload['time_period'].to_numpy()
    workload = workload.reset_index()
    workload4run = workload.loc[(workload['time_period'].isin(selected_time))]
    workload4run = workload4run.drop(columns=['time_period'])
    #print(workload4run)
    mutate_workload = mutation(workload4run)
    return workload_store, mutate_workload


def initial_create(loopingtime):
    s = [1500, 1500, 1500, 1500, 1500, 1500, 1500, 1500, 1500, 1500, 1500, 1500, 1500, 1500, 1500, 1500]
    print(s)
    n = str(loopingtime)
    file_name0 = "test" + n + ".jmx"
    file_name = "test.jmx"
    file = open(file_name, "r")
    data = file.readlines()
    k=0
    for i in range(0, len(data) - 1):
        if re.search("ConstantTimer.delay", data[i]):
            element = re.split('(<|>)', data[i])
            element[4] = str(s[k]).replace(".0","")
            #print(element[4])
            str_element = ""
            for e in element:
                str_element += e
            data[i] = str_element
        if re.search("RandomTimer.range", data[i]):
            element = re.split('(<|>)', data[i])
            element[4] = str("1000")
            str_element = ""
            for e in element:
                str_element += e
            data[i] = str_element
            k += 1

    file_write = open(file_name0, "w")
    file_write.writelines(data)
    file_write = open(file_name, "w")
    file_write.writelines(data)


def create_jmx_file(f_workload, loopingtime):
    s1 = round(30000 / f_workload['DELETE_URL2'])
    s2 = round(30000 / f_workload['GET_URL3'])
    s3 = round(30000 / f_workload['GET_URL8'])
    s4 = round(30000 / f_workload['GET_URL5'])
    s5 = round(30000 / f_workload['GET_URL7'])
    s6 = round(30000 / f_workload['GET_URL4'])
    s7 = round(30000 / f_workload['GET_URL6'])
    s8 = round(30000 / f_workload['POST_URL9'])
    sk0 = np.concatenate((s1[0:1], s2[0:1], s3[0:1], s4[0:1], s5[0:1], s6[0:1], s7[0:1], s8[0:1]))
    sk1 = np.concatenate((s1[1:2], s2[1:2], s3[1:2], s4[1:2], s5[1:2], s6[1:2], s7[1:2], s8[1:2]))
    for index, element in enumerate(sk0):
        sk0[index] = random.randint(50,5000)
    for index, element in enumerate(sk1):
        sk1[index] = random.randint(50,5000)
    sk2 = np.concatenate((sk0,sk0,sk0,sk0,sk0,sk0))
    sk3 = np.concatenate((sk1,sk1,sk1,sk1,sk1,sk1))
    s = np.concatenate((sk2,sk3))

    for index, element in enumerate(s):
        s[index] = random.randint(200,2000)

    n = str(loopingtime)
    file_name0 = "test" + n + ".jmx"
    file_name = "test.jmx"
    file = open(file_name, "r")
    data = file.readlines()
    k=0
    for i in range(0, len(data) - 1):
        if re.search("ConstantTimer.delay", data[i]):
            element = re.split('(<|>)', data[i])
            #print(str(s[k]))
            element[4] = str(s[k]).replace(".0","")
            #print(element[4])
            str_element = ""
            for e in element:
                str_element += e
            data[i] = str_element
        if re.search("RandomTimer.range", data[i]):
            element = re.split('(<|>)', data[i])
            rn = random.randint(100,500)
            element[4] = str(rn).replace(".0","")
            str_element = ""
            for e in element:
                str_element += e
            data[i] = str_element
            k += 1

    file_write = open(file_name0, "w")
    file_write.writelines(data)
    file_write = open(file_name, "w")
    file_write.writelines(data)
    return 0


def jmeter_function(jmeter_file_name):
    ssh_client = paramiko.SSHClient()
    ssh_client.load_system_host_keys()
    ssh_client.connect(hostname='10.128.0.35', username='yuanjiexia')
    ssh_client.exec_command('scp ~/.ssh/id_rsa yuanjiexia@10.128.0.45:~/' + jmeter_file_name + ' ~/')
    print('jmx sent')
    sleep(3)
    ssh_client.exec_command('sudo mv ~/test.jmx ~/database')
    print("runing jmeter...")
    ssh_client.exec_command("screen -d -m -L java -Xms1G -Xmx3G -jar /opt/jmeter/apache-jmeter-5.3/bin/ApacheJMeter.jar "
                                "-n -t ~/database/" + jmeter_file_name)


def pidstat_function(loop_time):
    os.system('pkill screen')
    os.system('screen -d -m -L pidstat -p ALL -u -r -d -h -I -l 1')


def main():
    
    #jmeter_function("test.jmx")
    #sleep(15)
    #pidstat_function(0)
    #print("running the first loop")
    #sleep(3660)
    #os.system('pkill screen')
    
    workload_store = []
    #workload_store = pd.read_csv("workload_store138.csv")
    jmx_file_name = "test.jmx"
    #today = date.today()
    #today = str(today)
    today = "2021-06-10" 
    log_file_address = '/home/yuanjiexia/openmrs-core/webapp/target/access-' + today + '.log'
    perf_file_address = '/home/yuanjiexia/screenlog.0'
    workload_store, mutate_workload = analysis_data(log_file_address, perf_file_address, workload_store,0)
    workload_store.to_csv('~/workload_store' + str(0)  + '.csv', index=False)
    print(len(workload_store))
    #initial_create(0)
    create_jmx_file(mutate_workload, 0)
    os.system('sudo mv screenlog.0 screenlog0.0')
    for loop_time in range(1, 300):
        #break
        print("looptime:"+str(loop_time))
        if localtime().tm_hour > 22:
            print("waiting date change")
            sleep(3600)
            
        os.system('cp ~/.OpenMRS/openmrs.log ~')
        sleep(3)
        os.system('mv openmrs.log openmrs.log.'+str(loop_time-1))
        os.system('mv openmrs.log.'+str(loop_time-1)+' ~/log')
        today = date.today()
        today = str(today)
        jmeter_function(jmx_file_name)
        sleep(3)
        pidstat_function(loop_time)
        sleep(1020)
        os.system('pkill screen')
        #os.chdir('openmrs-core/webapp')
        #os.system('screen -d -m mvn jetty:run')
        #os.chdir('../')
        #os.chdir('../')
        #sleep(120)
        log_file_address = '/home/yuanjiexia/openmrs-core/webapp/target/access-' + today + '.log'
        perf_file_address = '/home/yuanjiexia/screenlog.0'
        #os.system('sudo rm -rf /home/yuanjiexia/localhost_access_log.' + today + '.txt')
        #os.system('cp /home/yuanjiexia/openmrs-core/webapp/target/access-.' + today + '.txt ~')
        #os.system('mv /home/yuanjiexia/access-' + today + '.log /home/yuanjiexia/access-' + today + '.txt')
        #os.system('sudo chmod 777 localhost_access_log.' + today + '.txt')
        workload_store, mutate_workload = analysis_data(log_file_address, perf_file_address, workload_store,loop_time)
        workload_store.to_csv('~/workload_store' + str(loop_time)  + '.csv', index=False)
        create_jmx_file(mutate_workload, loop_time)
        print(len(workload_store))
        os.system('sudo mv screenlog.0 screenlog'+str(loop_time)+'.0')


if __name__ == "__main__":
    main()

