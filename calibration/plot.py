import csv
import sys
from os import path

import plotly.express as px
from dateutil.parser import parse

sys.path.append("./")

from config import DIVIDER_FACTOR

PATH = "./calibration-data/29.11.2022"

timestamp, voltage = zip(
    *(
        (parse(row["timestamp"]), float(row["voltage"]) * DIVIDER_FACTOR)
        for row in csv.DictReader(open(path.join(PATH, "voltage.csv"), "r", newline=""))
    )
)

fig = px.line(x=timestamp, y=voltage)
fig.show()
