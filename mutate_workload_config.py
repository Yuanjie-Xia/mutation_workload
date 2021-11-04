from load_file import load_file, generate_workload
import evaluate


class WorkLoad:
    def __init__(self, time_window_length, system, logFileAddress, perfFileAddress, loop_time, workload_store):
        self.time_window_length = time_window_length
        self.system = system
        self.loop_time = loop_time
        self.workload_store = workload_store
        self.log_data, self.perf_data = load_file(logFileAddress, perfFileAddress, time_window_length)
        self.signature, self.url_frequency = generate_workload(self)
        self.workload_signature, self.url_workload = generate_workload(self.signature)

    def evaluate_workload(self):
        self.workload_signature = evaluate.hierarchical_clustering(self.workload_signature)
        self.workload_signature = evaluate.measure_s(self.workload_signature)
        self.workload_signature, self.workload_store \
            = evaluate.measure_d(self.workload_store, self.signature, self.loop_time)

