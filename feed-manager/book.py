from collections import defaultdict
from order import Order
from decimal import Decimal
from time import time
from fees import FEES
import boto3

BOOK_DEPTH = 5

def book_age(book):
    return Decimal(time()) - book['timestamp'] / 1000

def parse_order(self, o):
    return Order(Decimal(o[0]), Decimal(o[1]))

def parse_book(self, orders):
    return map(lambda o:parse_order(o), orders[:BOOK_DEPTH])

class Book():
    def __init__(self, doc):
        self.bids = parse_book(doc['bids'])
        self.asks = parse_book(doc['asks'])
        self.exchange_name = doc['exchange']
        self.age = book_age(doc)
        self.pair = doc['pair']
        self.name = "%s-%s" % (self.exchange_name, self.pair)
        self.taker_fee = Decimal(FEES[self.exchange_name].taker) / Decimal(10000)

def process_data(ret, response):
    for doc in response['Items']:
        book = Book(doc)
        ret[book.pair].extend([book])

# returns map of pair => [list of books, one per exchange]
def query_all():
    ret = defaultdict(lambda:[])
    table = boto3.resource('dynamodb').Table('orderbooks')
    response = table.scan()
    process_data(ret, response)
    while response.get('LastEvaluatedKey'):
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        process_data(ret, response)

    return ret
