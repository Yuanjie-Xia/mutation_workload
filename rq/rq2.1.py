import pandas as pd
import keras
from keras import layers
import numpy as np
from statistics import median
from tqdm import tqdm

ori_b = []
for i in range(0, 143):
    url_b = pd.read_csv('data/baseline/urlfr/urlfr' + str(i) + '.csv')
    perf_b = pd.read_csv('data/baseline/perf/perf' + str(i) + '.csv')
    url_b['perf'] = perf_b['cpu']
    workload = pd.read_csv('data/baseline/workload/workload_store'+ str(i) +'.csv')
    url_b['cpulimit'] = workload['cpulimit'][len(workload['cpulimit'])-1]
    url_b['memorylimit'] = workload['memorylimit'][len(workload['memorylimit'])-1]
    if i == 0:
        ori_b = url_b
    else:
        ori_b = ori_b.append(url_b)

ori_b = ori_b.reset_index()
element_set = ['x1', 'x2', 'x3', 'x4', 'x5', 'x6', 'x7', 'x8', 'x9', 'x9b', 'x9c', 'x9d', 'cpulimit', 'memorylimit', 'perf']
ori_b = ori_b[element_set]

ori = []
for i in range(0, 143):
    url = pd.read_csv('data/mutate/urlfr/urlfr' + str(i) + '.csv')
    perf = pd.read_csv('data/mutate/perf/perf' + str(i) + '.csv')
    url['perf'] = perf['cpu']
    workload = pd.read_csv('data/mutate/workload/workload_store'+ str(i) +'.csv')
    url['cpulimit'] = workload['cpulimit'][len(workload['cpulimit'])-1]
    url['memorylimit'] = workload['memorylimit'][len(workload['memorylimit'])-1]
    if i == 0:
        ori = url
    else:
        ori = ori.append(url)

ori = ori.reset_index()
element_set = ['x1', 'x2', 'x3', 'x4', 'x5', 'x6', 'x7', 'x8', 'x9', 'x9b', 'x9c', 'x9d', 'cpulimit', 'memorylimit', 'perf']
ori = ori[element_set]

max_len = 13
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
model1 = keras.Model(inputs, predictions)
# Compile the model with binary crossentropy loss and an adam optimizer.
model.compile(loss="mse", optimizer="adam", metrics=["mape"])
model1.compile(loss="mse", optimizer="adam", metrics=["mape"])
error_tread = []
error_tread_r = []
for j in tqdm(range(1, 10)):
    training_set = ori.iloc[int((j - 1) * len(ori_b) / 10):int(j * len(ori_b) / 10)].copy()
    training_set_b = ori_b.iloc[int((j - 1) * len(ori_b) / 10):int(j * len(ori_b) / 10)].copy()
    training_set = training_set.reset_index()
    training_set_b = training_set_b.reset_index()
    sum = []
    sum_b = []
    for k in tqdm(range(len(training_set))):
        # model.compile(loss="mse", optimizer="adam", metrics=["mape"])
        # print(training_set.iloc[[55]])
        test_set = training_set.iloc[[k]]
        training_set_copy = training_set.copy()
        training_set_copy = training_set_copy.drop([k])
        training_set_x = training_set_copy.iloc[:, 0:13].to_numpy()
        training_set_x = np.expand_dims(training_set_x, axis=1)
        training_set_y = training_set_copy.iloc[:, 14].to_numpy()
        training_set_y = np.expand_dims(training_set_y, axis=1)
        test_set_x = test_set.iloc[:, 0:13].to_numpy()
        test_set_x = np.expand_dims(test_set_x, axis=1)
        test_set_y = test_set.iloc[:, 14].to_numpy()
        test_set_y = np.expand_dims(test_set_y, axis=1)
        model.fit(training_set_x, training_set_y, batch_size=32, epochs=100, verbose=0)
        result = model.predict(test_set_x)
        error = (result - test_set_y) / result
        sum.append(error)

    for q in tqdm(range(len(training_set_b))):
        # model.compile(loss="mse", optimizer="adam", metrics=["mape"])
        test_set_b = training_set_b.iloc[[q]]
        training_set_b_copy = training_set_b.copy()
        training_set_b_copy = training_set_b_copy.drop([q])
        training_set_x_b = training_set_b_copy.iloc[:, 0:13].to_numpy()
        training_set_x_b = np.expand_dims(training_set_x_b, axis=1)
        training_set_y_b = training_set_b_copy.iloc[:, 14].to_numpy()
        training_set_y_b = np.expand_dims(training_set_y_b, axis=1)
        test_set_x_b = test_set_b.iloc[:, 0:13].to_numpy()
        test_set_x_b = np.expand_dims(test_set_x_b, axis=1)
        test_set_y_b = test_set_b.iloc[:, 14].to_numpy()
        test_set_y_b = np.expand_dims(test_set_y_b, axis=1)
        model1.fit(training_set_x_b, training_set_y_b, batch_size=32, epochs=100, verbose=0)
        result = model1.predict(test_set_x_b)
        error = (result - test_set_y_b) / result
        sum_b.append(error)

    error_tread.append(median(sum))
    error_tread_r.append(median(sum_b))

error_tread.to_csv('error0.csv')
error_tread_r.to_csv('error1.csv')
print(error_tread)
print(error_tread_r)
