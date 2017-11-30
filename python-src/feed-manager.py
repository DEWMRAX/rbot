from ai import check_imbalance
from book import query_all
from logger import record_event
from collections import defaultdict
from decimal import Decimal
import boto3
import time

STALE_AGE = 60
ACTIVE_AGE = 6
INVOKE_THROTTLE = 4
REFRESH_RATE = 2

# lambda-name => timestamp of last update
book_age = defaultdict(lambda: 0)
last_invoked = defaultdict(lambda: 0)

with open('../markets.csv') as f:
    markets = [line.strip('\n').replace(',', '-') for line in f]

lambda_client = boto3.client('lambda')

def invoke_all(markets, reason):
    for market in markets:
        record_event("INVOKING,%s,%s" % (market, reason))
        lambda_client.invoke(InvocationType='Event', FunctionName=market)

def invoke_one(market, reason, waiting_time):
    record_event("INVOKING,%s,%s,%0.4f" % (market, reason, waiting_time))
    lambda_client.invoke(InvocationType='Event', FunctionName=market)

def throttled_invoke_one(market, reason, waiting_time):
    if time.time() > last_invoked[market] + INVOKE_THROTTLE:
        last_invoked[market] = time.time()
        invoke_one(market, reason, waiting_time)

while True:
    books = query_all()

    for pair, pair_books in books.items():
        for book in pair_books:
            book_age[book.name] = book.age

        if check_imbalance(pair_books, Decimal(80)) > Decimal(0):
            for book in pair_books:
                if book.age > ACTIVE_AGE:
                    throttled_invoke_one(book.name, 'ACTIVE', book.age - ACTIVE_AGE)

    for market in markets:
        market = market
        if book_age[market] > STALE_AGE:
           throttled_invoke_one(market, 'STALE', book_age[market] - STALE_AGE)

    record_event("SLEEPING,%s" % REFRESH_RATE)
    time.sleep(REFRESH_RATE)
