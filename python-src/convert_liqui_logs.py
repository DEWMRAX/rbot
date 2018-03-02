import os
import time
from datetime import datetime
from decimal import Decimal

FILE_IN='liqui_trades.txt'
FILE_OUT='libra_liqui_trades.txt'

def symbol_to_libra(symbol):
    s = symbol.upper()
    if s == 'BTC':
        return 'XBT'
    elif s == 'BCC':
        return 'BCH'
    else:
        return s

def side_to_libra(side):
    if side == 'sell':
        return 'exchangeAsk'
    elif side == 'buy':
        return 'exchangeBid'
    else:
        print "UNKNOWN TYPE"
        assert(False)

def timestamp_to_libra(t):
    t = t.replace(' ', 'T')
    return t + 'Z'

os.remove(FILE_OUT) if os.path.exists(FILE_OUT) else None

with open(FILE_OUT, 'a') as f:
    f.write("type,base_asset,base_amount,counter_asset,counter_amount,rate,fee_asset,fee_amount,tx_ts,exchange_name,exchange_order_id,exchange_tx_id\n")

with open(FILE_IN, 'r') as fin:
    with open(FILE_OUT, 'a') as fout:

        for line in fin:
            [timestamp, pair, order_id, amount, rate, side, transaction_id, unused] = line.split(',')

            base_asset = symbol_to_libra(pair.split('_')[0])
            counter_asset = symbol_to_libra(pair.split('_')[1])
            base_amount = Decimal(amount)
            rate = Decimal(rate)
            counter_amount = base_amount * rate
            fee_amount = base_amount * Decimal('0.0025')
            ts = timestamp_to_libra(timestamp)
            side = side_to_libra(side)

            fout.write("%s,%s,%0.8f,%s,%0.8f,%0.8f,%s,%0.8f,%s,liqui,%s,%s\n" % (side, base_asset, base_amount, counter_asset, counter_amount, rate, base_asset, fee_amount, ts, order_id, transaction_id))
