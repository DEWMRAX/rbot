from ai import check_imbalance
from book import query_all
from logger import record_event
from collections import defaultdict
from decimal import Decimal
from threading import Thread
import boto3
import time

STALE_AGE = 30
ACTIVE_AGE = 1
INVOKE_THROTTLE = 2

# lambda-name => timestamp of last update
book_age = defaultdict(lambda: 99999999)
last_invoked = defaultdict(lambda: 0)

lambda_client = boto3.client('lambda')

def invoke_one(market, reason, waiting_time, throttle=True):
    if (time.time() > last_invoked[market] + INVOKE_THROTTLE or not throttle) and not market.startswith('LIQUI'):
        last_invoked[market] = time.time()
        record_event("INVOKING,%s,%s,%0.4f" % (market, reason, waiting_time))
        t = Thread(target=lambda_client.invoke, name=market, kwargs=dict(InvocationType='Event', FunctionName=market))
        t.start()

def invoke_all(markets, reason):
    for market in markets:
        invoke_one(str(market), reason, 0, throttle=False)

if __name__ == '__main__':
    with open('../markets.csv') as f:
        all_markets = [line.strip('\n').replace(',', '-') for line in f]

    while True:
        record_event("QUERY_ALL_START")
        books = query_all()
        record_event("QUERY_ALL_END")

        for pair, pair_books in books.items():
            for book in pair_books:
                book_age[book.name] = book.age
            if check_imbalance(pair_books) > Decimal(0):
                for book in pair_books:
                    if book.age > ACTIVE_AGE:
                        invoke_one(book.name, 'ACTIVE', book.age)

        for market in all_markets:
            market = market
            if book_age[market] > STALE_AGE:
                invoke_one(market, 'STALE', book_age[market])

        record_event("SLEEPING,1")
        time.sleep(1)
