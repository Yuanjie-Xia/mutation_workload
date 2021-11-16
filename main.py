import paramiko

import mutate_workload_config
import os
from time import sleep

logFileAddress = 'test_set/localhost_access_log.2021-11-05.txt'
perfFileAddress = 'test_set/screenlog.0'


def main():
    window_size = 10
    workload = mutate_workload_config.WorkLoad(window_size, 'TeaStore', logFileAddress=logFileAddress,
                                               perfFileAddress=perfFileAddress,
                                               loop_time=0)
    workload.init_config()
    os.system('docker run --cpus="' + workload.config[0] + '" -m=' + workload.config[1] +
              'GB -e "DB_HOST=teastore-db" -p 8080:8080 -d --link teastore-db:teastore-db '
              '--name teastore-all descartesresearch/teastore-all')
    os.system('screen -d -m -L pidstat -p ALL -u -r -d -h -I -l ' + str(window_size))
    os.system("locust -f runtest_init.py --headless --users 1 --spawn-rate 1 --run-time=30s -H http://localhost:8080")
    os.system('pkill screen')
    # move file out docker
    workload.load_data()
    workload.set_config()
    workload.b_cnn()
    workload.evaluate_workload()
    workload.sort_workload()
    workload.generate_running_file()
    workload.set_config()
    # send ratio.csv

    for loop_time in range(1, 100):
        os.system('sudo mv screenlog.0 screenlog' + str(loop_time) + '.0')
        os.system('docker rm teastore-all')
        os.system('docker run --cpus="' + workload.config[0] + '" -m=' + workload.config[1] +
                  'GB -e "DB_HOST=teastore-db" -p 8080:8080 -d --link teastore-db:teastore-db '
                  '--name teastore-all descartesresearch/teastore-all')
        ssh_client = paramiko.SSHClient()
        ssh_client.load_system_host_keys()
        ssh_client.connect(hostname='192.168.165.203', username='yxia', password='zengyi')
        ssh_client.exec_command('scp ~/mutation_workload/ratio.csv yxia@192.168.165.203:~/mutation_workload')
        sleep(60)
        os.system('screen -d -m -L pidstat -p ALL -u -r -d -h -I -l ' + str(window_size))
        ssh_client.exec_command("locust -f ~/mutation_workload/runtest1.py --headless --users 1 "
                                "--spawn-rate 1 --run-time=30s -H http://localhost:8080")
        ssh_client.exec_command("locust -f ~/mutation_workload/runtest2.py --headless --users 1 "
                                "--spawn-rate 1 --run-time=30s -H http://localhost:8080")
        os.system('pkill screen')
        # move file out docker
        workload = mutate_workload_config.WorkLoad(window_size, 'TeaStore', logFileAddress=logFileAddress,
                                                   perfFileAddress=perfFileAddress,
                                                   loop_time=loop_time)
        workload.load_data()
        workload.init_config()
        workload.b_cnn()
        workload.evaluate_workload()
        workload.sort_workload()
        workload.generate_running_file()
        # send ratio.csv


if __name__ == "__main__":
    main()
