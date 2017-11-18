from collections import defaultdict
from decimal import Decimal
from flask import Flask, redirect, url_for
import boto3
import time

MAX_AGE = 200

app = Flask(__name__)

table = boto3.resource('dynamodb', region_name='us-east-1').Table('orderbooks')

def book_age(book):
    return Decimal(time.time()) - book['timestamp'] / 1000

def book_to_string(item, depth):
    age = book_age(item)
    ret = "%s %s AGE: %0.3f<br>" % (item['exchange'], item['pair'], age)

    for i in xrange(depth, 0, -1):
        if i-1 < len(item['asks']):
            quote = item['asks'][i-1]
            ret += "%0.8f x %0.8f<br>" % (Decimal(quote[0]), Decimal(quote[1]))

    ret += "==============================<br>"

    for i in xrange(0, depth):
        if i < len(item['bids']):
            quote = item['bids'][i]
            ret += "%0.8f x %0.8f<br>" % (Decimal(quote[0]), Decimal(quote[1]))

    return ret

def check_imbalance(bidder, seller):

    bids = bidder['bids']
    asks = seller['asks']
    bids_idx = 0
    bid_price = bids[0][0]
    asks_idx = 0
    ask_price = asks[0][0]
    qty = Decimal(0)
    total_profit = Decimal(0)
    ret = "<br>"

    ret += "best ask %0.8f @ %s<br>" % (asks[0][0], seller['exchange'])
    ret += "best bid %0.8f @ %s<br>" % (bids[0][0], bidder['exchange'])

    while(1):
        if bids_idx >= len(bids) or asks_idx >= len(asks):
            break

        bid = bids[bids_idx]
        ask = asks[asks_idx]

        friction = Decimal('0.005')
        if bid[0] <= ask[0]:
            ret += "markets uncrossed<br>"
            break

        benefit = bid[0] - ask[0]
        pct_benefit = benefit / bid[0]
        ret += "benefit / friction / net : %0.8f / %0.8f / %0.8f<br>" % (pct_benefit * Decimal(100), friction * Decimal(100), (pct_benefit - friction) * Decimal(100))

        if pct_benefit <= friction:
            break

        bid_price = bid[0]
        ask_price = ask[0]

        if bid[1] > ask[1]:
            qty += Decimal(ask[1])
            bids[bids_idx] = (bid[0], bid[1] - ask[1])
            profit = (pct_benefit - friction) * ask[0] * ask[1] * Decimal(1000)
            total_profit += profit

            ret += "STACKING QTY %d/%d added: %0.8f, total: %0.8f<br>" % (bids_idx, asks_idx, ask[1], qty)
            # print "STACKED PROFIT: %0.8f mBTC" % profit

            asks_idx += 1
        else:
            qty += Decimal(bid[1])
            asks[asks_idx] = (ask[0], ask[1] - bid[1])
            profit = (pct_benefit - friction) * bid[0] * bid[1] * Decimal(1000)
            total_profit += profit

            ret += "STACKING QTY %d/%d added: %0.8f, total: %0.8f<br>" % (bids_idx, asks_idx, bid[1], qty)
            # print "STACKED PROFIT: %0.8f mBTC" % profit

            bids_idx += 1

    if qty > Decimal(0):

        ret += "ACTIONABLE IMBALANCE of %0.8f<br>" % qty
        ret += "AVAILABLE PROFIT of %0.8f mBTC/mETH/mUSDT<br>" % total_profit

    return (ret, total_profit)

def best_bidder(books):
    eligible_books = filter(lambda book:book_age(book) < Decimal(MAX_AGE), books)
    if len(eligible_books) == 0:
        return None

    best = eligible_books[0]
    for book in eligible_books:
        if len(best['bids']) == 0:
            best = book
        elif len(book['bids']) > 0 and book['bids'][0][0] > best['bids'][0][0]:
            best = book

    return best

def best_seller(books):
    eligible_books = filter(lambda book:book_age(book) < Decimal(MAX_AGE), books)
    if len(eligible_books) == 0:
        return None

    best = eligible_books[0]
    for book in eligible_books:
        if len(best['asks']) == 0:
            best = book
        elif len(book['asks']) > 0 and book['asks'][0][0] < best['asks'][0][0]:
            best = book

    return best

def parse_quote(quote):
    return [Decimal(quote[0]), Decimal(quote[1])]

def scan_table():
    response = table.scan()
    books = response['Items']
    while response.get('LastEvaluatedKey'):
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        books.extend(respond['Items'])

    return books

def parse_books(books):
    for book in books:
        book['asks'] = map(lambda ask:parse_quote(ask), book['asks'])
        book['bids'] = map(lambda bid:parse_quote(bid), book['bids'])

@app.route('/check/<pair>')
def show_books(pair):
    fil = boto3.dynamodb.conditions.Key('pair').eq(pair)
    books = table.scan(FilterExpression=fil)['Items']
    parse_books(books)

    ret = "<br><br>".join(map(lambda item:book_to_string(item, 5), books))

    bidder = best_bidder(books)
    seller = best_seller(books)

    if bidder and seller:
        return check_imbalance(bidder, seller)[0] + "<br><br>" + ret
    else:
        return ret

@app.route('/best')
def best_book():
    best = None
    best_books = None
    pairs = defaultdict(lambda:[])
    books = scan_table()
    parse_books(books)
    for book in books:
        pairs[book['pair']].extend([book])

    for pair,pair_books in pairs.items():
        bidder = best_bidder(pair_books)
        seller = best_seller(pair_books)

        if bidder and seller:
            imbalance = check_imbalance(bidder, seller)
            if best is None or best[1] < imbalance[1]:
                best = imbalance
                best_books = pair_books
    return redirect(url_for('show_books', pair=best_books[0]['pair']))
    return best[0] + "<br><br>" + "<br><br>".join(map(lambda item:book_to_string(item, 5), best_books))

if __name__ == '__main__':
  app.run()
