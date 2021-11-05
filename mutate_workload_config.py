from load_file import load_file, generate_workload
import evaluate


class WorkLoad:
    def __init__(self, time_window_length, system, logFileAddress, perfFileAddress,
                 loop_time, workload_store=[], log_data=[], perf_data=[],
                 signature=[], url_fr=[]):

        self.time_window_length = time_window_length
        self.logFileAddress = logFileAddress
        self.perfFileAddress = perfFileAddress
        self.system = system
        self.loop_time = loop_time
        self.workload_store = workload_store
        self.log_data = log_data
        self.perf_data = perf_data
        self.signature = signature
        self.url_fr = url_fr

    def load_data(self):
        self.log_data, self.perf_data = load_file(self.logFileAddress,
                                                  self.perfFileAddress, self.time_window_length)

        self.signature, self.url_fr = generate_workload(self.log_data)
        # print(self.signature)
        # print(self.url_fr)

    def evaluate_workload(self):
        self.signature = evaluate.hierarchical_clustering(self.signature)
        self.signature = evaluate.measure_s(self.signature, self.perf_data)
        self.signature, self.workload_store \
            = evaluate.measure_d(self.workload_store, self.url_fr, self.loop_time)
        print(self.signature)

