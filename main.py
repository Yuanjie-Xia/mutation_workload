import mutate_workload_config

logFileAddress = 'test_set/localhost_access_log.2021-11-05.txt'
perfFileAddress = 'test_set/screenlog.0'


def main():
    workload = mutate_workload_config.WorkLoad(10, 'TeaStore', logFileAddress=logFileAddress,
                                               perfFileAddress=perfFileAddress,
                                               loop_time=0)
    workload.load_data()
    workload.evaluate_workload()


if __name__ == "__main__":
    main()
