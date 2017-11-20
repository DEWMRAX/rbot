from order import Order
from decimal import Decimal

MAX_AGE = Decimal(80)

def check_imbalance_internal(bidder, seller):

    bids = bidder.bids
    asks = seller.asks
    bids_idx = 0
    bid_price = bids[0].price
    asks_idx = 0
    ask_price = asks[0].quantity
    imbalance_quantity = Decimal(0)
    total_profit = Decimal(0)
    # ret = "<br>"

    # ret += "best ask %0.8f @ %s<br>" % (asks[0].price, seller.exchange_name)
    # ret += "best bid %0.8f @ %s<br>" % (bids[0].price, bidder.exchange_name)

    while(1):
        if bids_idx >= len(bids) or asks_idx >= len(asks):
            break

        bid = bids[bids_idx]
        ask = asks[asks_idx]

        friction = bidder.taker_fee + seller.taker_fee
        if bid.price <= ask.price:
            # ret += "markets uncrossed<br>"
            break

        benefit = bid.price - ask.price
        pct_benefit = benefit / bid.price
        # ret += "benefit / friction / net : %0.8f / %0.8f / %0.8f<br>" % (pct_benefit * Decimal(100), friction * Decimal(100), (pct_benefit - friction) * Decimal(100))

        if pct_benefit <= friction:
            break

        if bid.quantity > ask.quantity:
            imbalance_quantity += ask.quantity
            bids[bids_idx] = Order(bid.price, bid.quantity - ask.quantity)
            profit = (pct_benefit - friction) * ask.price * ask.quantity * Decimal(1000)
            total_profit += profit

            # ret += "STACKING QTY %d/%d added: %0.8f, total: %0.8f<br>" % (bids_idx, asks_idx, ask[1], imbalance_quantity)
            # print "STACKED PROFIT: %0.8f mBTC" % profit

            asks_idx += 1
        else:
            imbalance_quantity += bid.quantity
            asks[asks_idx] = Order(ask.price, ask.quantity - bid.quantity)
            profit = (pct_benefit - friction) * bid.price * bid.quantity * Decimal(1000)
            total_profit += profit

            # ret += "STACKING QTY %d/%d added: %0.8f, total: %0.8f<br>" % (bids_idx, asks_idx, bid[1], imbalance_quantity)
            # print "STACKED PROFIT: %0.8f mBTC" % profit

            bids_idx += 1

    # if imbalance_quantity > Decimal(0):
    #
    #     ret += "ACTIONABLE IMBALANCE of %0.8f<br>" % imbalance_quantity
    #     ret += "AVAILABLE PROFIT of %0.8f mBTC/mETH/mUSDT<br>" % total_profit

    return total_profit

def best_bidder(books):
    eligible_books = filter(lambda book:book_age(book) < MAX_AGE, books)
    if len(eligible_books) == 0:
        return None

    best = eligible_books[0]
    for book in eligible_books:
        if len(best.bids) == 0:
            best = book
        elif len(book.bids) > 0 and book.bids[0].price > best.bids[0].price:
            best = book

    return best

def best_seller(books):
    eligible_books = filter(lambda book:book_age(book) < MAX_AGE, books)
    if len(eligible_books) == 0:
        return None

    best = eligible_books[0]
    for book in eligible_books:
        if len(best.asks) == 0:
            best = book
        elif len(book.asks) > 0 and book.asks[0].price < best.asks[0].price:
            best = book

    return best

def check_imbalance(books):
    bidder = best_bidder(books)
    seller = best_seller(books)

    if bidder and seller:
        return check_imbalance_internal(bidder, seller)
    else:
        return ("Insufficient book data")
