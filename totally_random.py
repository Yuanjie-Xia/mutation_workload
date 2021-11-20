import pandas as pd
import random

w1 = [0] * 13
w2 = [0] * 13
d = [w1, w2]
df = pd.DataFrame(d, columns=['x1', 'x2', 'x3', 'x4', 'x5', 'x6', 'x7', 'x8', 'x9', 'x9a', 'x9b', 'x9c', 'x9d'])
for i in range(0, df.shape[0]):
    line = df.iloc[[i]].to_numpy()[0]
    max_value = max(line)
    v = random.randint(0, 4)
    for index, element in enumerate(line):
        line[index] = random.randrange(10, 100)
    df.iloc[[i]] = [line]
    df['x9a'] = df['x9']
df.to_csv('ratio.csv')
