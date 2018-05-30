from ai import near_crossed
from book import query_all
from logger import record_event
from collections import defaultdict
from decimal import Decimal
from threading import Thread
import boto3
import time
import json

STALE_AGE = 20
ACTIVE_AGE = 0
INVOKE_THROTTLE = 2

MAKER_SYMBOLS = ['ICN','REP','MLN','XLM','BTC']

# lambda-name => timestamp of last update
book_age = defaultdict(lambda: 99999999)
last_invoked = defaultdict(lambda: 0)

lambda_client = boto3.client('lambda')

def invoke_one(market, reason, waiting_time, throttle=True):
    if (time.time() > last_invoked[market] + INVOKE_THROTTLE or not throttle) and not market.startswith('LIQUI'):
        last_invoked[market] = time.time()
        record_event("INVOKING,%s,%s,%0.4f" % (market, reason, waiting_time))
        (exchange, token, currency) = market.split('-')
        event = dict(exchange=exchange, token=token, currency=currency)
        t = Thread(target=lambda_client.invoke, name='FEED-HANDLER', kwargs=dict(InvocationType='Event', FunctionName='FEED-HANDLER', Payload=json.dumps(event)))
        t.start()

def invoke_all(markets, reason):
    for market in markets:
        invoke_one(str(market), reason, 0, throttle=False)

if __name__ == '__main__':
    with open('../markets.csv') as f:
        all_markets = [line.strip('\n').replace(',', '-') for line in f]

    while True:
        record_event("QUERY_ALL_START")
        books = query_all(tablename='orderbooks-test')
        record_event("QUERY_ALL_END")

        for pair, pair_books in books.items():
            for book in pair_books:
                book_age[book.name] = book.age

            if near_crossed(pair_books) or any(map(lambda sym:pair.startswith(sym), MAKER_SYMBOLS)):
                for book in pair_books:
                    if book.age > ACTIVE_AGE:
                        invoke_one(book.name, 'ACTIVE', book.age)

        for market in all_markets:
            market = market
            if book_age[market] > STALE_AGE:
                invoke_one(market, 'STALE', book_age[market])

        record_event("SLEEPING,1")
        time.sleep(1)
