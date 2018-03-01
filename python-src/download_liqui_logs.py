import liqui
import os
import time
from datetime import datetime
from decimal import Decimal

PAGE_SIZE=1000
FILE_PATH='liqui_trades.txt'

l = liqui.Liqui()

i = 0
trades = []

cutofftime = 1512603900

def symbol_to_libra(symbol):
    s = symbol.upper()
    if s == 'BTC':
        return 'XBT'
    elif s == 'BCC':
        return 'BCH'
    else:
        return s

def type_to_libra(typ):
    if typ == 'sell':
        return 'exchangeAsk'
    elif typ == 'buy':
        return 'exchangeBid'
    else:
        print "UNKNOWN TYPE"
        assert(False)

def timestamp_to_libra(t):
    return datetime.utcfromtimestamp(t).isoformat() + 'Z'

os.remove(FILE_PATH) if os.path.exists(FILE_PATH) else None

with open(FILE_PATH, 'a') as f:
    f.write("type,base_asset,base_amount,counter_asset,counter_amount,rate,fee_asset,fee_amount,tx_ts,exchange_name,exchange_order_id,exchange_tx_id\n")

def print_history(trades):
    with open(FILE_PATH, 'a') as f:
        for trade in trades:
            base_asset = symbol_to_libra(trade.pair.split('_')[0])
            counter_asset = symbol_to_libra(trade.pair.split('_')[1])
            base_amount = Decimal(trade.amount)
            rate = Decimal(trade.rate)
            counter_amount = base_amount * rate
            fee_amount = base_amount * Decimal('0.0025')
            ts = timestamp_to_libra(trade.timestamp)
            typ = type_to_libra(trade.type)
            f.write("%s,%s,%0.8f,%s,%0.8f,%0.8f,%s,%0.8f,%s,liqui,%s,%s\n" % (typ, base_asset, base_amount, counter_asset, counter_amount, rate, base_asset, fee_amount, ts, trade.order_id, trade.transaction_id))

while(i == 0 or len(trades) > 0):
    print "PAGE %d" % i

    from_id = 0
    if len(trades) > 0:
        from_id = max(map(lambda t:t.transaction_id, trades)) + 1

    print "FROM ID: %d" % from_id

    while True:
        try:
            trades = l.tapi.tradeHistory(count_number=PAGE_SIZE, from_id=from_id, order='ASC', end=cutofftime, connection=l.conn)
            break
        except Exception as e:
            print e
            print "CALL FAILED"
            time.sleep(5)

    print_history(trades)

    i += 1
