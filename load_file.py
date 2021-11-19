import re
import pandas as pd
import math
from time import ctime, gmtime, sleep
from datetime import datetime, timedelta


def transfer2type(system, action, url):
    url = str(url)
    # print(url)
    action = str(action)
    if system == 'OpenMRS':
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
                # print(url)

        if action == "DELETE":
            url = "DELETE_URL2"

        if re.search("person", url):
            if re.search("person\\?q=", url):
                url = "GET_URL3"
            else:
                url = "GET_URL8"
    if system == 'TeaStore':
        if action == "GET":
            if re.search("webui", url):
                url = url.replace("/tools.descartes.teastore.webui", "")
                if re.search("/status", url):
                    url = "x1"
                if re.search("/profile", url):
                    url = "x2"
                if re.search("/database", url):
                    url = "x3"
                if re.search("/login", url):
                    url = "x4"
                if re.search("/category", url):
                    url = "x5"
                if re.search("/product", url):
                    url = "x6"
                if re.search("/cart", url):
                    url = "x7"
                if re.search("teastore", url):
                    url = "subservice"
                if url == "/":
                    url = "x8"
        if action == "POST":
            if re.search("loginAction", url):
                url = "x9"
            # if re.search("logout", url):
            #    url = "x9a"
            if re.search("category", url):
                url = "x9b"
            if re.search("cartAction", url):
                url = "x9c"
            if re.search("order", url):
                url = "x9d"
    return url


def load_file(log_address, perf_address, period_size):
    # only suitable for Tomcat execution log
    perf_data = open(perf_address, 'r')
    split_list = []
    i = 0

    for line in perf_data:
        if line.__contains__('docker-java-home'):
            # print(line)
            element_perf = line.split()
            while i == 0:
                start_time = int(element_perf[0]) + 20
                k = start_time % 10
                i = i + 1
            try:
                if int(element_perf[0]) % 10 == k:
                    time_interval = int(element_perf[0]) - start_time
                    time_period = math.floor(time_interval / period_size) + 1
                    cpu = float(element_perf[7])
                    rss = float(element_perf[12])
                    memory = float(element_perf[13])
                    if time_period > 0:
                        split_list.append([time_period, cpu, rss, memory])
            except ValueError:
                print("cannot convert to int in "+str(line))
            finally:
                pass

    perf = pd.DataFrame(split_list, columns=['time_period', 'cpu', 'rss', 'memory'])
    # print(perf)
    log_data = open(log_address, 'r')
    # print(log_data)
    split_list = []
    normal_start_time = gmtime(start_time)
    transfer_start_time = timedelta(days=normal_start_time.tm_mday, hours=normal_start_time.tm_hour,
                                    minutes=normal_start_time.tm_min, seconds=normal_start_time.tm_sec)
    print('this loop start time:')
    print(transfer_start_time)
    for line in log_data:
        # print(line)
        elements = line.split(' ')
        # print(len(elements))
        time = elements[3][1:]
        time_part = time.replace(':', '/').split('/')
        day = int(time_part[0])
        hour = int(time_part[3])
        minute = int(time_part[4])
        second = int(time_part[5])

        current_time = timedelta(days=day, hours=hour, minutes=minute, seconds=second)
        # print(current_time)
        duration = (current_time - transfer_start_time).total_seconds()
        # Designed as the pidstat run after jmeter start
        time_period = math.floor(duration / period_size) + 1
        # print(time_period)
        if time_period > 60:
            break
        if time_period < 1:
            continue
        action = elements[5][1:]
        url = elements[6]
        url = transfer2type('TeaStore', action, url)
        # print(url)
        response = elements[8]
        split_list.append([action, url, response, time_period])

    log = pd.DataFrame(split_list, columns=['action', 'url', 'respondCode', 'time_period'])
    log = log[log['url'].isin(['x1', 'x2', 'x3', 'x4', 'x5', 'x6', 'x7', 'x8', 'x9', 'x9b', 'x9c', 'x9d'])]
    # search_value = ['POST', 'GET']
    # log = log.loc[log.url.str.contains('|'.join(search_value)), :]
    # print(log)
    # print(perf)
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
    url_workload = workload_count.pivot(index='time_period', columns='url', values='n').fillna(0)
    url_set = ['x1', 'x2', 'x3', 'x4', 'x5', 'x6', 'x7', 'x8', 'x9', 'x9b', 'x9c', 'x9d']
    if len(url_workload.columns) < 12:
        for index, element in enumerate(url_set):
            if url_set[index] not in url_workload.columns:
                url_workload.insert(index, url_set[index], [0] * url_workload.shape[0])

    return workload_signature, url_workload
