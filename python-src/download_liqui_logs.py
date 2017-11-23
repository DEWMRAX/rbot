import liqui
import os
import time 

PAGE_SIZE=1000
FILE_PATH='liqui_trades.txt'

l = liqui.Liqui()

i = 0
trades = []

os.remove(FILE_PATH) if os.path.exists(FILE_PATH) else None
def print_history(t):
    with open(FILE_PATH, 'a') as f:
        for i in range(0,len(t)):
            f.write("%s,%s,%s,%s,%s,%s,%s,%s\n" % (t[i].timestamp, t[i].pair, t[i].order_id, t[i].amount, t[i].rate, t[i].type, t[i].transaction_id, t[i].is_your_order))

while(i == 0 or len(trades) > 0):
    print "PAGE %d" % i

    from_id = 0
    if len(trades) > 0:
        from_id = max(map(lambda t:t.transaction_id, trades)) + 1

    print "FROM: %d" % from_id

    while True:
        try:
            trades = l.tapi.tradeHistory(count_number=PAGE_SIZE, from_id=from_id, order='ASC', connection=l.conn)
            break
        except Exception as e:
            print e
            print "CALL FAILED"
            time.sleep(5)

    print_history(trades)

    i += 1
