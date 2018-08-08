from datetime import datetime
from sys import argv

prev_dt = None
count = 0

for line in open(argv[1]):
    tokens = line.split(",")
    timestamp = tokens[0] + ":" + tokens[1]
    dt = datetime.strptime(timestamp, "%m-%d:%H:%M:%S")
    if prev_dt:
        delta = (dt - prev_dt).total_seconds()
        if delta > 60:
            print timestamp
            print delta

    prev_dt = dt
