from load_file import load_file


class workload:
    def __init__(self, time_window_length, system, logFileAddress, perfFileAddress):
        self.time_window_length = time_window_length
        self.system = system
        self.log_data, self.perf_data = load_file(logFileAddress, perfFileAddress, time_window_length)
