import mutate_workload_config
import os
from time import sleep
from datetime import datetime
import urllib
import pytz
import random
import pandas as pd


def main():
    workload_store = []
    today = datetime.now(pytz.utc).date()
    logFileAddress = '/home/users/yzeng/localhost_access_log.' + str(today) + '.txt'
    perfFileAddress = '/home/users/yzeng/mutation_workload/screenlog.0'
    window_size = 10
    workload = mutate_workload_config.WorkLoad(window_size, 'TeaStore', logFileAddress=logFileAddress,
                                               perfFileAddress=perfFileAddress,
                                               loop_time=0, workload_store=workload_store)
    workload.init_config()
    os.system('sudo docker stop teastore-all')
    os.system('sudo docker rm teastore-all')
    os.system('sudo docker run --cpus=' + str(workload.config[0]) + ' -m=' + str(workload.config[1]) +
              'GB -e "DB_HOST=sense02" -p 8080:8080 -d '
              '--name teastore-all descartesresearch/teastore-all')
    os.system('sudo docker cp ~/mutation_workload/server.xml teastore-all:/usr/local/tomcat/conf')
    print('server config sent')
    sleep(2)
    os.system('sudo docker restart teastore-all')
    for i in range(1, 100):
        try:
            code = urllib.request.urlopen("http://192.168.165.201:8080/tools.descartes.teastore.webui").getcode()
            print(code)
            if code == 200:
                break
        except urllib.error.URLError:
            print("web not avaliable yet")
        finally:
            sleep(3)
            pass
        if i > 90:
            print("application cannot start")
    os.system('rm -rf /home/users/yzeng/mutation_workload/screenlog.0')
    os.system('screen -S pids -d -m -L pidstat -p ALL -u -r -d -h -H -I -l ' + str(window_size))
    print("pidstat started")
    os.system('sshpass -p \'xyj0731\' ssh yxia@sense03 \'~/.local/bin/locust -f ~/mutation_workload/runtest_init.py '
              '--headless --users 10 --spawn-rate 1 --run-time=600s -H http://192.168.165.201:8080\'')
    print("running command end here")
    os.system('screen -X -S "pids" quit')
    os.system('rm -rf ' + logFileAddress)
    os.system('sudo docker cp teastore-all:/usr/local/tomcat/logs/localhost_access_log.' + str(today) + '.txt ~/')
    os.system('sudo chmod 777 ~/localhost_access_log.' + str(today) + '.txt ~/')
    workload.load_data()
    workload.b_cnn()
    workload.evaluate_workload()
    workload.sort_workload()
    workload.generate_running_file()

    df = pd.read_csv('ratio.csv')
    for i in range(0, df.shape[0]):
        line = df.iloc[[i]].to_numpy()[0]
        for index, element in enumerate(line):
            # if line[index] > 70:
            #    line[index] = 10
            #    max_value = max(line)
            line[index] = random.randrange(10, 50)
        df.iloc[[i]] = [line]
    df.to_csv('ratio.csv')

    workload.config = [random.randrange(4, 8)/2, random.randrange(2, 8)]

    print('configuration:')
    print(workload.config)
    os.system('sshpass -p \'xyj0731\' scp ratio.csv yxia@sense03:~/mutation_workload')

    for loop_time in range(1, 144):
        print('looptime:' + str(loop_time))
        if datetime.now(pytz.utc).hour >= 23:
            if datetime.now(pytz.utc).minute >= 45:
                print('wait date change')
                sleep(900)
        today = datetime.now(pytz.utc).date()
        logFileAddress = '/home/users/yzeng/localhost_access_log.' + str(today) + '.txt'
        perfFileAddress = '/home/users/yzeng/mutation_workload/screenlog.0'
        history_config = workload.config.copy()
        workload_store = workload.workload_store.copy()
        workload = mutate_workload_config.WorkLoad(window_size, 'TeaStore', logFileAddress=logFileAddress,
                                                   perfFileAddress=perfFileAddress,
                                                   loop_time=loop_time, workload_store=workload_store)
        workload.config = history_config
        workload.workload_store = workload_store
        os.system('sudo mv ~/mutation_workload/screenlog.0 ~/screenlog' + str(loop_time) + '.0')
        os.system('sudo docker stop teastore-all')
        sleep(10)
        os.system('sudo docker rm teastore-all')
        os.system('sudo docker run --cpus="' + str(workload.config[0]) + '" -m=' + str(workload.config[1]) +
                  'GB -e "DB_HOST=sense02" -p 8080:8080 -d '
                  '--name teastore-all descartesresearch/teastore-all')
        os.system('sudo docker cp ~/mutation_workload/server.xml teastore-all:/usr/local/tomcat/conf')
        os.system('sudo docker restart teastore-all')
        for i in range(1, 100):
            try:
                code = urllib.request.urlopen("http://192.168.165.201:8080/tools.descartes.teastore.webui").getcode()
                print(code)
                if code == 200:
                    break
            except urllib.error.URLError:
                print("web not avaliable yet")
            finally:
                sleep(3)
                pass
            if i > 90:
                print("application cannot start")
        os.system('rm -rf /home/users/yzeng/mutation_workload/screenlog.0')
        os.system('screen -S pids -d -m -L pidstat -p ALL -u -r -d -h -H -I -l ' + str(window_size))
        os.system('sshpass -p \'xyj0731\' ssh yxia@sense03 \'~/.local/bin/locust -f ~/mutation_workload/runtest1.py '
                  '--headless --users 10 --spawn-rate 1 --run-time=300s -H http://192.168.165.201:8080\'')
        os.system('sshpass -p \'xyj0731\' ssh yxia@sense03 \'~/.local/bin/locust -f ~/mutation_workload/runtest2.py '
                  '--headless --users 10 --spawn-rate 1 --run-time=300s -H http://192.168.165.201:8080\'')
        os.system('screen -X -S "pids" quit')
        os.system('rm -rf ' + logFileAddress)
        os.system('sudo docker cp teastore-all:/usr/local/tomcat/logs/localhost_access_log.' + str(today) + '.txt ~/')
        os.system('sudo chmod 777 ~/localhost_access_log.' + str(today) + '.txt ~/')
        workload.load_data()
        workload.b_cnn()
        workload.evaluate_workload()
        workload.sort_workload()
        workload.generate_running_file()
        df = pd.read_csv('ratio.csv')

        for i in range(0, df.shape[0]):
            line = df.iloc[[i]].to_numpy()[0]
            for index, element in enumerate(line):
                # if line[index] > 70:
                #    line[index] = 10
                #    max_value = max(line)
                line[index] = random.randrange(10, 50)
            df.iloc[[i]] = [line]
        df.to_csv('ratio.csv')

        workload.config = [random.randrange(4, 8)/2, random.randrange(2, 8)]
        print(workload.config)

        os.system('sshpass -p \'xyj0731\' scp ratio.csv yxia@sense03:~/mutation_workload')


if __name__ == "__main__":
    main()
