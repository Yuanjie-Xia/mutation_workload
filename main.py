import mutate_workload_config
import os
from time import sleep

logFileAddress = 'test_set/localhost_access_log.2021-11-05.txt'
perfFileAddress = 'test_set/screenlog.0'


def main():
    workload = mutate_workload_config.WorkLoad(10, 'TeaStore', logFileAddress=logFileAddress,
                                               perfFileAddress=perfFileAddress,
                                               loop_time=0)
    workload.load_data()
    workload.evaluate_workload()
    workload.sort_workload()
    workload.generate_running_file()
    os.system("locust -f runtest1.py --headless --users 1 --spawn-rate 1 --run-time=30s -H http://localhost:8080")
    os.system("locust -f runtest2.py --headless --users 1 --spawn-rate 1 --run-time=30s -H http://localhost:8080")


if __name__ == "__main__":
    main()
