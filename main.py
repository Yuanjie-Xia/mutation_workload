import mutate_workload_config

logFileAddress = '~/openmrs-core/webapp/target/access.log'
perfFileAddress = '~/screenlog.0'


def main():
    workload = mutate_workload_config.WorkLoad(10, 'TeaStore', logFileAddress, perfFileAddress)


if __name__ == "__main__":
    main()
