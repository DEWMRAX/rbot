from fees import FEES
import datetime

def record_event(s):
    timestamp = '{:%m-%d,%H:%M:%S}'.format(datetime.datetime.now())
    with open("events.txt", "a") as events:
        events.write("%s,%s\n" % (timestamp, s))

def record_trade(s):
    timestamp = '{:%m-%d,%H:%M:%S}'.format(datetime.datetime.now())
    with open("trades.txt", "a") as trades:
        trades.write("%s,%s\n" % (timestamp, s))
