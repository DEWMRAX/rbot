from collections import defaultdict
from order import Order
from decimal import Decimal
from time import time
from fees import FEES
from boto3.dynamodb.conditions import Key
import boto3

BOOK_DEPTH = 10

def book_age(book):
    return Decimal(time()) - book['timestamp'] / 1000

def parse_order(o):
    return Order(Decimal(o[0]), Decimal(o[1]))

def parse_book(orders):
    return map(lambda o:parse_order(o), orders[:BOOK_DEPTH])

class Book():
    def __init__(self, doc):
        self.bids = parse_book(doc['bids'])
        self.asks = parse_book(doc['asks'])
        self.exchange_name = doc['exchange']
        self.age = book_age(doc)
        self.pair = doc['pair']
        self.name = "%s-%s" % (self.exchange_name, self.pair)
        self.taker_fee = FEES[self.exchange_name].taker

    def __str__(self):
        return self.name

    def print_depth(self, depth):
        print
        print "%s %s" % (self.exchange_name, self.pair)

        for i in xrange(depth, 0, -1):
            if i-1 < len(self.asks):
                quote = self.asks[i-1]
                print "%0.8f x %0.8f" % (quote.price, quote.quantity)

        print "=============================="

        for i in xrange(0, depth):
            if i < len(self.bids):
                quote = self.bids[i]
                print "%0.8f x %0.8f" % (quote.price, quote.quantity)


def process_data(ret, response):
    for doc in response['Items']:
        book = Book(doc)
        ret[book.pair].extend([book])

# returns map of pair => [list of books, one per exchange]
def query_all(tablename='orderbooks'):
    ret = defaultdict(lambda:[])
    table = boto3.resource('dynamodb').Table(tablename)
    response = table.scan()
    process_data(ret, response)
    while response.get('LastEvaluatedKey'):
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        process_data(ret, response)

    return ret

def query_pair(pair, tablename='orderbooks'):
    filtr = Key('pair').eq(str(pair))
    table = boto3.resource('dynamodb').Table(tablename)
    return map(lambda doc:Book(doc), table.scan(FilterExpression=filtr)['Items'])
