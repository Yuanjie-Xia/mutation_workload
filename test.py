import os
import urllib
from time import sleep

import mutate_workload_config


def main():
    workload_store = []
    logFileAddress = 'test_set/localhost_access_log.2021-11-05.txt'
    perfFileAddress = 'test_set/screenlog.0'
    window_size = 10
    workload = mutate_workload_config.WorkLoad(window_size, 'TeaStore', logFileAddress=logFileAddress,
                                               perfFileAddress=perfFileAddress,
                                               loop_time=0, workload_store=workload_store)
    workload.init_config()
    workload.load_data()
    workload.set_config()
    workload.b_cnn()
    workload.evaluate_workload()
    workload.sort_workload()
    workload.generate_running_file()
    print(workload.config_change_rate)
    workload.set_config()


if __name__ == "__main__":
    main()