import re
import pandas as pd
import math
from time import ctime, localtime, sleep
from datetime import date, timedelta


def transfer2type(system, action, url):
    if system == 'OpenMRS':
        url = str(url)
        # print(url)
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
                # print(url)

        if action == "DELETE":
            url = "DELETE_URL2"

        if re.search("person", url):
            if re.search("person\\?q=", url):
                url = "GET_URL3"
            else:
                url = "GET_URL8"
    return url


def load_file(log_address, perf_address, period_size):
    perf_data = open(perf_address, 'r')
    split_list = []
    i = 0

    for line in perf_data:
        if line.__contains__('openjdk'):
            # print(line)
            element_perf = line.split()
            while i == 0:
                start_time = int(element_perf[0])
                i = i + 1

            time_interval = int(element_perf[0]) - start_time
            time_period = math.floor(time_interval / (period_size * 3)) + 1
            time_round = math.floor(time_interval / period_size) + 1
            cpu = float(element_perf[6])
            rss = float(element_perf[11])
            memory = float(element_perf[12])
            if time_round % 3 == 1:
                split_list.append([time_period, cpu, rss, memory])

    perf = pd.DataFrame(split_list, columns=['time_period', 'cpu', 'rss', 'memory'])
    # print(perf)
    log_data = open(log_address, 'r')
    # print(log_data)
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
        # print(line)
        elements = line.split()
        # print(len(elements))
        if len(elements) == 14:
            day = int(elements[4][9:11])
            hour = int(elements[5][0:2])
            minute = int(elements[5][3:5])
            second = int(elements[5][6:8])
            current_time = timedelta(days=day, hours=hour, minutes=minute, seconds=second)
            # print(current_time)
            duration = (current_time - transfer_start_time).total_seconds()
            # Designed as the pidstat run after jmeter start
            time_period = math.floor(duration / (3 * period_size)) + 1
            # print(time_period)
            if time_period > 12:
                break
            if time_period < 1:
                continue
            action = elements[6][1:]
            url = elements[7]
            url = transfer2type(action, url)
            # print(url)
            response = elements[9]
            split_list.append([action, url, response, time_period])

    log = pd.DataFrame(split_list, columns=['action', 'url', 'respondCode', 'time_period'])
    search_value = ['POST', 'DELETE', 'GET']
    log = log.loc[log.url.str.contains('|'.join(search_value)), :]
    return log, perf
