import mutate_workload_config
import os
from time import sleep

logFileAddress = 'test_set/localhost_access_log.2021-11-05.txt'
perfFileAddress = 'test_set/screenlog.0'


def main():
    window_size = 10
    os.system('screen -d -m -L pidstat -p ALL -u -r -d -h -I -l ' + str(window_size))
    os.system("locust -f runtest_init.py --headless --users 1 --spawn-rate 1 --run-time=30s -H http://localhost:8080")
    os.system('pkill screen')
    workload = mutate_workload_config.WorkLoad(window_size, 'TeaStore', logFileAddress=logFileAddress,
                                               perfFileAddress=perfFileAddress,
                                               loop_time=0)
    workload.load_data()
    workload.init_config()
    workload.b_cnn()
    workload.evaluate_workload()
    workload.sort_workload()
    workload.generate_running_file()

    for loop_time in range(1, 100):
        os.system('sudo mv screenlog.0 screenlog' + str(loop_time) + '.0')
        os.system('screen -d -m -L pidstat -p ALL -u -r -d -h -I -l ' + str(window_size))
        os.system("locust -f runtest1.py --headless --users 1 --spawn-rate 1 --run-time=30s -H http://localhost:8080")
        os.system("locust -f runtest2.py --headless --users 1 --spawn-rate 1 --run-time=30s -H http://localhost:8080")
        os.system('pkill screen')
        workload = mutate_workload_config.WorkLoad(window_size, 'TeaStore', logFileAddress=logFileAddress,
                                                   perfFileAddress=perfFileAddress,
                                                   loop_time=loop_time)
        workload.load_data()
        workload.init_config()
        workload.b_cnn()
        workload.evaluate_workload()
        workload.sort_workload()
        workload.generate_running_file()


if __name__ == "__main__":
    main()
