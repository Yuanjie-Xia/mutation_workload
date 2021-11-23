import pandas as pd
import keras
from keras import layers
import numpy as np
from statistics import median

ori = []
for i in range(0, 143):
    url = pd.read_csv('data/mutate/urlfr/urlfr' + str(i) + '.csv')
    perf = pd.read_csv('data/mutate/perf/perf' + str(i) + '.csv')
    url['perf'] = perf['cpu']
    workload = pd.read_csv('data/mutate/workload/workload_store'+ str(i) +'.csv')
    url['cpulimit'] = workload['cpulimit'][0]
    url['memorylimit'] = workload['memorylimit'][0]
    if i == 0:
        ori = url
    else:
        ori = ori.append(url)

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
# Compile the model with binary crossentropy loss and an adam optimizer.
model.compile(loss="mse", optimizer="adam", metrics=["mape"])

training_set = ori.iloc[0:int(len(ori)*0.5)]
test_set = ori.iloc[int(len(ori)*0.5):len(ori)]
training_set_x = training_set.iloc[:, 0:13].to_numpy()
training_set_x = np.expand_dims(training_set_x, axis=1)
training_set_y = training_set.iloc[:, 14].to_numpy()
training_set_y = np.expand_dims(training_set_y, axis=1)
test_set_x = test_set.iloc[:, 0:13].to_numpy()
test_set_x = np.expand_dims(test_set_x, axis=1)
test_set_y = test_set.iloc[:, 14].to_numpy()
test_set_y = np.expand_dims(test_set_y, axis=1)

model.fit(training_set_x, training_set_y, batch_size=32, epochs=100)
result = model.predict(test_set_x)
error = (result-test_set_y)/result
print(median(error))
