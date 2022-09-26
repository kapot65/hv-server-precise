import csv
from datetime import timedelta
from itertools import chain
import sys
from os import path
from dateutil.parser import parse

import plotly.graph_objects as go
import numpy as np

sys.path.append('./')

from config import DIVIDER_FACTOR

PATH = "./calibration-data/26.09.2022"

output_voltages = list(
    (parse(row['timestamp']), 
    float(row['voltage']) * DIVIDER_FACTOR) for row in 
        csv.DictReader(open(path.join(PATH, 'voltage.csv'), 'r', newline=''))
    )

input_voltages = list(
    (parse(row['timestamp']), 
    float(row['voltage_scaled'])) for row in 
        csv.DictReader(open(path.join(PATH, 'voltage_sets.csv'), 'r', newline=''))
    )

def __group_voltages(input_, output):
    for idx, input_step in enumerate(input_):
        start_ts = input_step[0] + timedelta(seconds=30)
        end_ts = input_[idx + 1][0] \
            if idx != len(input_) - 1 \
                else start_ts + timedelta(hours=1)
        out_v =  filter(lambda voltage: voltage[0] >= start_ts and voltage[0] < end_ts, output)
        yield [(input_step[1], v[1]) for v in out_v]

prepared_data = chain(*__group_voltages(input_voltages, output_voltages))

x, y = zip(*prepared_data)

a, b =  np.polyfit(x, y, 1)

print(a, b)

fig = go.Figure()
fig.add_traces(go.Scatter(x=x, y=[(a * p + b) for p in x], mode="lines+markers"))
fig.add_traces(go.Scatter(x=x, y=y, mode="markers"))
fig.show()
