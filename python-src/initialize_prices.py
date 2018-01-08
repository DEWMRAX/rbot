# TODO this command should live in the commands directory, need to figure out the import thing

import ai
from book import query_all
from decimal import Decimal
from pymongo import MongoClient

price_collection = MongoClient().arbot.prices

books = query_all()

for pair, pair_book in books.iteritems():
    (token, currency) = pair.split('-')
    if currency == 'BTC' or (token == 'BTC' and currency == 'USDT') or (currency == 'USD' and token == 'BTC'):
        price = (ai.best_bidder(pair_book).bids[0].price + ai.best_seller(pair_book).asks[0].price) / 2
        print pair, price
        symbol = token
        if token == 'BTC':
            symbol = currency
            price = Decimal(1) / price
        price_collection.update({'symbol':symbol}, {'$set':{'price':float(price)}}, upsert=True)
