from load_file import load_file, generate_workload
import evaluate
import numpy as np
import random
import keras
from keras import layers
import math


class WorkLoad:
    def __init__(self, time_window_length, system, logFileAddress, perfFileAddress,
                 loop_time, workload_store, log_data=[], perf_data=[],
                 signature=[], url_fr=[], selected_workload=[], config=[], model=[], config_change_rate=0.5):
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
        self.config = config
        self.model = model
        self.config_change_rate = config_change_rate

    def set_config(self):
        v = random.randrange(0, 100)/100
        if v >= self.config_change_rate:
            self.config[0] = random.randrange(4, 8)/2
            # cpu cores number
        v = random.randrange(0, 100)/100
        if v >= self.config_change_rate:
            self.config[1] = random.randrange(2, 8)
            # memory usage

    def init_config(self):
        self.config = [2, 6]
        # cpu limit and memory limit

    def load_data(self):
        self.log_data, self.perf_data = load_file(self.logFileAddress,
                                                  self.perfFileAddress, self.time_window_length)

        self.signature, self.url_fr = generate_workload(self.log_data)
        # print(self.signature)
        # print(self.url_fr)

    def evaluate_workload(self):
        self.signature = evaluate.hierarchical_clustering(self.signature)
        self.signature, self.config_change_rate = evaluate.measure_s(self.signature, self.perf_data,
                                                                     self.config, self.model)
        self.url_fr, self.workload_store \
            = evaluate.measure_d(self.workload_store, self.url_fr, self.config, self.loop_time)
        # self.workload_store['cpulimit'] = self.config[0]
        # self.workload_store['memorylimit'] = self.config[1]
        self.workload_store.to_csv("/home/users/yzeng/workload/workload_store" + str(self.loop_time) + ".csv")
        self.signature['diversity'] = self.url_fr['diversity']
        self.signature['measurement'] = abs(self.signature['stability']) + abs(self.signature['diversity'])
        self.url_fr['measurement'] = self.signature['measurement']
        self.url_fr['cluster'] = self.signature['cluster']
        self.signature.to_csv("/home/users/yzeng/signature/siginature" + str(self.loop_time) + ".csv")
        print('signature:')
        print(self.signature)
        self.perf_data.to_csv("/home/users/yzeng/perf/perf" + str(self.loop_time) + ".csv")
        print('perf:')
        print(self.perf_data)
        self.url_fr.to_csv("/home/users/yzeng/urlfr/urlfr" + str(self.loop_time) + ".csv")
        print('url frenquency:')
        print(self.url_fr)

    def sort_workload(self):
        # sort and mutate workload
        selection_df = self.url_fr.sort_values('measurement', ascending=False).drop_duplicates(['cluster'])
        # selection_df = self.signature.sort_values(by=['measurement'], ascending=False)
        if len(selection_df) >= 2:
            self.selected_workload = selection_df[0:2]
        else:
            self.selected_workload = selection_df
        self.selected_workload['x9'] = self.selected_workload['x9'] / 2
        self.selected_workload.insert(10, "x9a", self.selected_workload['x9'])
        self.selected_workload['x8'] = self.selected_workload['x8'] - self.selected_workload['x9'] - \
                                       self.selected_workload['x9b']
        if 'x2302' in self.signature.columns:
            self.selected_workload['x8'] = self.selected_workload['x8'] - self.signature['x2302']
        self.selected_workload = \
            self.selected_workload.loc[:, self.selected_workload.columns.str.startswith('x')]

        print("selected workload before mutate:")
        print(self.selected_workload)
        for i in range(0, np.size(self.selected_workload.columns)):
            v = random.randint(0, 1)
            if v == 1:
                line = self.selected_workload[self.selected_workload.columns[i]].to_numpy()
                line[0], line[1] = line[1], line[0]
                self.selected_workload[self.selected_workload.columns[i]] = line

        for i in range(0, np.size(self.selected_workload.columns)):
            v = random.randint(0, 4)
            line = self.selected_workload[self.selected_workload.columns[i]].to_numpy()
            if v == 1:
                v0 = random.randint(0, 1)
                if int(line[v0] - 10) > 0:
                    line[v0] = random.randint(int(line[v0] - 10), int(line[v0] + 10))
                else:
                    line[v0] = random.randint(0, int(line[v0] + 10))
        self.selected_workload[self.selected_workload.columns[i]] = line

        for i in range(0, self.selected_workload.shape[0]):
            line = self.selected_workload.iloc[[i]].to_numpy()[0]
            max_value = max(line)
            v = random.randint(0, 4)
            if v == 1:
                v1 = random.randint(0, len(line)-1)
                v2 = random.randint(0, len(line)-1)
                line[v1], line[v2] = line[v2], line[v1]

            for index, element in enumerate(line):
                # if line[index] > 70:
                #    line[index] = 10
                #    max_value = max(line)
                line[index] = 100 * math.log((line[index] / max_value) + 1, 10)
                if line[index] < 3:
                    line[index] = 5
            self.selected_workload.iloc[[i]] = [line]
        self.selected_workload['x8'] = self.selected_workload['x8']/3
        print("selected_workload:")
        print(self.selected_workload)

    def generate_running_file(self):
        self.selected_workload.to_csv("ratio.csv", index=False)

    def b_cnn(self):
        max_len = len(self.signature.loc[:, self.signature.columns.str.startswith('x')].columns) + len(self.config)
        # A integer input for vocab indices.
        # inputs = keras.Input(shape=(series_input.shape[1], 1,))
        inputs = keras.Input(shape=(1, max_len), dtype="float32")
        # Conv1D + global max pooling
        x = layers.Conv1D(128, 3, padding="same", activation="relu", strides=3)(inputs)
        x = layers.Conv1D(128, 3, padding="same", activation="relu", strides=3)(x)
        x = layers.GlobalMaxPooling1D()(x)

        # We add a vanilla hidden layer:
        x = layers.Dense(128, activation="relu")(x)
        x = layers.Dropout(0.5)(x)

        # We project onto a single unit output layer, and squash it with a sigmoid:
        predictions = layers.Dense(1, activation="linear", name="predictions")(x)

        model = keras.Model(inputs, predictions)

        # Compile the model with binary crossentropy loss and an adam optimizer.
        model.compile(loss="mse", optimizer="adam", metrics=["mape"])
        self.model = model
