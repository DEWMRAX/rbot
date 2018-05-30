import datetime, sys, time, signal
from collections import namedtuple, defaultdict
from decimal import Decimal, Context, ROUND_FLOOR, ROUND_CEILING
from pymongo import MongoClient

import poloniex, bittrex, binance, liqui, kraken, GDAX, itbit, bitflyer, exchange
from book import query_all, query_pair
from feed_manager import invoke_all
from logger import record_event, record_trade
from order import Order
from pair import ALL_PAIRS, ALL_SYMBOLS, pair_factory

Edge = namedtuple('Edge', ['rate','exchange','label'])
edges = defaultdict(lambda: dict())

def effective_bid(book):
    if len(book.bids) == 0:
        return Decimal(0)

    return book.bids[0].price * (Decimal(1) - book.taker_fee)

def effective_ask(book):
    if len(book.asks) == 0:
        return Decimal(999999999999)

    return book.asks[0].price * (Decimal(1) + book.taker_fee)

def best_bid(books):
    return max(map(lambda book: (book.exchange_name, effective_bid(book)), books), key=lambda (name,price):price)

def best_ask(books):
    return min(map(lambda book: (book.exchange_name, effective_ask(book)), books), key=lambda (name,price):price)

for pair, pair_books in query_all(tablename='orderbooks-test').iteritems():
    (token, currency) = pair.split('-')
    # pair = pair_factory(token, currency)

    (exchange_name, price) = best_bid(pair_books)
    edges[token][currency] = Edge(price, exchange_name, "%s->%s" % (token, currency))

    (exchange_name, price) = best_ask(pair_books)
    edges[currency][token] = Edge(Decimal(1) / price, exchange_name, "%s->%s" % (currency, token))

print edges

HOME = 'BTC'
MAX_LOOP = int(sys.argv[1])

node_val = defaultdict(lambda: None)
node_from = defaultdict(lambda: None)
q = set([HOME])
next_q = set()
node_val[HOME] = Decimal(1)
node_from[HOME] = [HOME]

while(len(q) > 0):
    print q
    print node_val
    for node in q:
        for dest, edge in edges[node].iteritems():
            if len(node_from[node]) >= MAX_LOOP and dest is not HOME:
                continue
            exchange_val = node_val[node] * edge.rate
            if node_val[dest] is None or exchange_val > node_val[dest]:
                node_val[dest] = exchange_val
                if dest not in node_from[node]:
                    next_q.add(dest)
                node_from[dest] = node_from[node] + [dest]

    q = next_q
    next_q = set()

print node_val[HOME]
print node_from[HOME]

for i in range(0, len(node_from[HOME])-1):
    print edges[node_from[HOME][i]][node_from[HOME][i+1]]
