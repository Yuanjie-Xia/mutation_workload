from load_file import load_file, generate_workload
import evaluate
import numpy as np
import random


class WorkLoad:
    def __init__(self, time_window_length, system, logFileAddress, perfFileAddress,
                 loop_time, workload_store=[], log_data=[], perf_data=[],
                 signature=[], url_fr=[], selected_workload=[]):
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
        self.selected_workload = selected_workload

    def load_data(self):
        self.log_data, self.perf_data = load_file(self.logFileAddress,
                                                  self.perfFileAddress, self.time_window_length)

        self.signature, self.url_fr = generate_workload(self.log_data)
        # print(self.signature)
        # print(self.url_fr)

    def evaluate_workload(self):
        self.signature = evaluate.hierarchical_clustering(self.signature)
        self.signature = evaluate.measure_s(self.signature, self.perf_data)
        self.url_fr, self.workload_store \
            = evaluate.measure_d(self.workload_store, self.url_fr, self.loop_time)
        self.signature['diversity'] = self.url_fr['diversity']
        self.signature['measurement'] = abs(self.signature['stability']) + abs(self.signature['diversity'])
        self.url_fr['measurement'] = self.signature['measurement']
        self.url_fr['cluster'] = self.signature['cluster']
        print(self.url_fr)

    def sort_workload(self):
        # sort and mutate workload
        selection_df = self.signature.sort_values('measurement', ascending=False).drop_duplicates(['cluster'])
        # selection_df = self.signature.sort_values(by=['measurement'], ascending=False)
        if len(selection_df) >= 2:
            self.selected_workload = selection_df[0:2]
        else:
            self.selected_workload = selection_df

        self.selected_workload = \
            self.selected_workload.loc[:, self.selected_workload.columns.str.startswith('x')]
        for i in range(0, np.size(self.selected_workload.columns)):
            v = random.randint(0, 1)
            if v == 1:
                line = self.selected_workload[self.selected_workload.columns[i]].to_numpy()
                temp = line[1]
                line[1] = line[0]
                line[0] = temp
                self.selected_workload[self.selected_workload.columns[i]] = line

    def generate_running_file(self):
        pass
