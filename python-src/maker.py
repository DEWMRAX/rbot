import datetime, sys, time
from collections import namedtuple
from decimal import Decimal, Context, ROUND_FLOOR, ROUND_CEILING
from pymongo import MongoClient

import poloniex, bittrex, binance, liqui, kraken, GDAX, itbit, bitflyer, exchange
from book import query_all, query_pair
from feed_manager import invoke_all
from logger import record_event, record_trade
from order import Order
from pair import ALL_PAIRS, ALL_SYMBOLS, pair_factory

MAX_BOOK_AGE = 3.33
MAX_RECOVERY_ATTEMPTS = 10
TRANSFER_THRESHOLD_LOW=Decimal('.22')
TRANSFER_THRESHOLD_HIGH=Decimal('2.5')
DRAWDOWN_AMOUNT=Decimal('.42') # how much to leave on an exchange we are withdrawing from
DRAWUP_AMOUNT=Decimal('1.75') # how much to target on an exchange we are transferring to
BALANCE_ACCURACY=Decimal('0.02')
LIQUI_NAV_PERCENTAGE_MAX=Decimal('0.01')

DISABLE_TRADING = False
UPDATE_TARGET_BALANCE = False
UPDATE_ALL_TARGET_BALANCE = False
REPAIR_BALANCES = False
INITIALIZE_BALANCE_CACHE = False

if len(sys.argv) > 1:
    if sys.argv[1] == 'repair_balances':
        REPAIR_BALANCES = True
    if sys.argv[1] == 'initialize_balance_cache':
        INITIALIZE_BALANCE_CACHE = True
    if sys.argv[1] == 'zero_balances':
        UPDATE_TARGET_BALANCE = True
        if len(sys.argv) > 2 and sys.argv[2] == 'all':
            UPDATE_ALL_TARGET_BALANCE = True

open_trades_collection = MongoClient().arbot.trades
open_transfers_collection = MongoClient().arbot.transfers
target_balance_collection = MongoClient().arbot.targets
price_collection = MongoClient().arbot.prices
maker_orders_collection = MongoClient().arbot.maker_orders

def panic(response):
    print response.status
    print response.error
    print response
    print "PANIC! At The Disco"
    sys.exit(1)

def sleep(duration, reason):
    record_event("SLEEPING,%d,%s" % (duration, reason))
    time.sleep(duration)

# order determines execution ordering, assumes more liquidity at the latter exchange
#   and that earlier exchanges are faster responding
exchanges = [bittrex.Bittrex(), binance.Binance(), kraken.Kraken(), poloniex.Poloniex()]
def get_exchange_handler(name):
    return filter(lambda exchange:exchange.name == name, exchanges)[0]

if INITIALIZE_BALANCE_CACHE:
    for exchange in exchanges:
        exchange.unprotected_refresh_balances()
    sys.exit(0)

PRICE = {'BTC' : Decimal(1)}
for record in price_collection.find({}):
    PRICE[record['symbol']] = Decimal(record['price'])

def near_equals(x, y, threshold='0.001'):
    if x < Decimal('0.0001'):
        return y < Decimal('0.0001')
    return (abs(x - y) / x) < Decimal(threshold)

def get_exchanges(pair):
    return filter(lambda exch:exch.has_pair(pair), exchanges)

def total_balance(symbol):
    return sum(map(lambda exch:exch.get_balance(symbol), exchanges))

OVERRIDE_TARGET_BALANCE = {
    'LIQUI':{
        'BTC': Decimal(0.8),
        'ETH': Decimal(17),
        'LTC': Decimal(7),
        'BCH': Decimal(1.7)},
    'KRAKEN':{
        'BTC':Decimal(5)
}}
def has_override(exchange, symbol):
    return exchange.name in OVERRIDE_TARGET_BALANCE and symbol in OVERRIDE_TARGET_BALANCE[exchange.name]

TARGET_BALANCE = dict()
TOTAL_TARGET_BALANCE = dict()
for symbol in ALL_SYMBOLS:
    doc = target_balance_collection.find_one({'symbol':symbol})
    TARGET_BALANCE[symbol] = dict()
    TOTAL_TARGET_BALANCE[symbol] = Decimal(doc['balance'])
    remaining_balance = Decimal(doc['balance'])

    # First, check all target overrides
    for exchange in exchanges:
        if has_override(exchange, symbol):
            TARGET_BALANCE[symbol][exchange.name] = OVERRIDE_TARGET_BALANCE[exchange.name][symbol]
            remaining_balance -= TARGET_BALANCE[symbol][exchange.name]

    remaining_count = len(filter(lambda exch:symbol in exch.symbols and not has_override(exch, symbol), exchanges))

    for exchange in exchanges:
        if not has_override(exchange, symbol):
            TARGET_BALANCE[symbol][exchange.name] = remaining_balance / remaining_count

def total_balance_incl_pending(symbol):
    confirmed = total_balance(symbol)
    target = TOTAL_TARGET_BALANCE[symbol]

    if (confirmed > target or near_equals(confirmed, target, BALANCE_ACCURACY)):
        return confirmed

    transfer = open_transfers_collection.find_one({'symbol':symbol, 'active':True})
    if transfer:
        return confirmed + Decimal(transfer['amount'])

    return confirmed

if UPDATE_TARGET_BALANCE:
    for exch in exchanges:
        exch.unprotected_refresh_balances()

    symbol_list = ALL_SYMBOLS if UPDATE_ALL_TARGET_BALANCE else ['BTC','ETH','USDT','USD']

    for symbol in symbol_list:
        balance = "%0.8f" % total_balance_incl_pending(symbol)
        target_balance_collection.update({'symbol':symbol}, {'$set':{'balance':balance}}, upsert=True)

    sys.exit(0)
    sleep(3, 'PRECAUTION') # don't forget to throttle if decide not to shut down after

def target_nav():
    return sum(map(lambda symbol: PRICE[symbol]*TOTAL_TARGET_BALANCE[symbol], ALL_SYMBOLS))

def balances_nav(balance_func):
    return sum(map(lambda symbol: PRICE[symbol]*balance_func(symbol), ALL_SYMBOLS))

def exchange_nav(exch):
    return balances_nav(lambda symbol:exch.get_balance(symbol))

def exchange_nav_incl_pending(exch):
    total = exchange_nav(exch)
    for doc in open_transfers_collection.find({'active':True,'to':exch.name}):
        total = total + Decimal(doc['amount']) * PRICE[doc['symbol']]

    return total

def exchange_nav_as_percentage_of_total(exch):
    exchange_nav = exchange_nav_incl_pending(exch)
    total_nav = balances_nav(total_balance_incl_pending)
    return exchange_nav / total_nav

# revenue in mBTC
def arbitrage_revenue():
    nav = balances_nav(total_balance_incl_pending)
    return 1000 * (nav-target_nav())

def balances_string_helper(balance_func):
    nav = balances_nav(balance_func)
    usd_nav = nav / PRICE['USD'] / Decimal(1e6)
    return ("%0.4f,%0.4f,%0.8f," % (1000*(nav-target_nav()), usd_nav, nav)) + ','.join(map(lambda symbol: "%0.8f" % balance_func(symbol), ALL_SYMBOLS))

def balances_string_in_btc():
    nav = balances_nav(total_balance_incl_pending)
    usd_nav = nav / PRICE['USD'] / Decimal(1e6)
    return ("%0.4f,%0.4f,%0.8f," % (1000*(nav-target_nav()), usd_nav, nav)) + ','.join(map(lambda symbol: "%0.8f" % (PRICE[symbol] * total_balance_incl_pending(symbol)), ALL_SYMBOLS))

def balances_string():
    return balances_string_helper(total_balance_incl_pending)

def balances_string_confirmed():
    return balances_string_helper(total_balance)

def balances_detail():
    return ','.join(map(lambda exch:','.join(map(lambda symbol: "%0.8f" % exch.get_balance(symbol), ALL_SYMBOLS)), exchanges))

def execute_trade(buyer, seller, pair, quantity, expected_profit, bid, ask):
    assert(DISABLE_TRADING == False)

    starting_currency_balance = total_balance(pair.currency)
    starting_token_balance = total_balance(pair.token)

    trade_doc = {'buyer':buyer.name, 'seller':seller.name, 'quantity':"%0.8f" % quantity,
                 'token':pair.token, 'currency':pair.currency, 'bid':"%0.8f" % bid, 'ask':"%0.8f" % ask,
                 'token_balance':"%0.8f" % starting_token_balance, 'recovery_attempts':0}
    open_trades_id = open_trades_collection.insert_one(trade_doc).inserted_id

    info = balances_string() + ",%s,%s,%s,%s,%0.8f,%0.8f,%0.8f,%0.8f" % (buyer.name, seller.name, pair.token, pair.currency, quantity, bid, ask, expected_profit)

    record_event("AI,%s" % info)
    # this comment is useful to turn off trading
    # open_trades_collection.delete_one({'_id':open_trades_id})
    # return

    # exchanges ordering influences execution strategy
    buyer_idx = exchanges.index(buyer)
    seller_idx = exchanges.index(seller)

    if buyer_idx > seller_idx:
        bought_quantity = seller.trade_ioc(pair, 'buy', ask, quantity, 'AI') * (1 - seller.get_fee(pair)) # fee deducted from purchase
        if bought_quantity < pair.min_quantity(): # order gone before we got there
            record_event("RACE,%0.8f" % bought_quantity)
            open_trades_collection.delete_one({'_id':open_trades_id})
            return

        market_price = Decimal("%0.6f" % (bid * Decimal('0.9')))
        sold_quantity = quantity = buyer.trade_ioc(pair, 'sell', market_price, bought_quantity, 'AI') # execute second order at effectively market price
        print sold_quantity
        print bought_quantity
        assert(near_equals(sold_quantity, bought_quantity, '0.05'))

    else:
        sold_quantity = buyer.trade_ioc(pair, 'sell', bid, quantity, 'AI')
        if sold_quantity < pair.min_quantity(): # order gone before we got there
            record_event("RACE,%0.8f" % sold_quantity)
            open_trades_collection.delete_one({'_id':open_trades_id})
            return

        market_price = Decimal("%0.6f" % (ask * Decimal('1.1')))
        bought_quantity = quantity = seller.trade_ioc(pair, 'buy', market_price, sold_quantity / (1 - seller.get_fee(pair)), 'AI') * (1 - seller.get_fee(pair))  # execute second order at effectively market price
        print sold_quantity
        print bought_quantity
        assert(near_equals(sold_quantity, bought_quantity, '0.05'))

    open_trades_collection.delete_one({'_id':open_trades_id})

    sleep(2, 'BALANCE_UPDATE') # give exchanges (bittrex) chance to update balances
    buyer.unprotected_refresh_balances()
    seller.unprotected_refresh_balances()

    ending_currency_balance = total_balance(pair.currency)
    actual_profit = (ending_currency_balance - starting_currency_balance) * Decimal(1000) * PRICE[pair.currency]

    exec_report = info + ",%0.8f,%0.8f\n" % (quantity, actual_profit)

    record_trade(exec_report)

    info = balances_string() + ",%s,%s,%s,%s,%0.8f,%0.8f,%0.8f,%0.8f" % (buyer.name, seller.name, pair.token, pair.currency, quantity, bid, ask, expected_profit * Decimal(1000))

    record_event("AI_CLOSE,%s" % info)

def eligible_books_filter(books):
    return filter(lambda book:book.exchange_name not in ['LIQUI','GDAX'] and book.age < MAX_BOOK_AGE and get_exchange_handler(book.exchange_name).active and book.pair.split('-')[0] in get_exchange_handler(book.exchange_name).symbols, books)

def effective_bid(book):
    return book.bids[0].price * (Decimal(1) - book.taker_fee)

def best_bidder(books):
    eligible_books = eligible_books_filter(books)
    if len(eligible_books) == 0:
        return None

    best = eligible_books[0]
    for book in eligible_books:
        if len(best.bids) == 0:
            best = book
        elif len(book.bids) > 0 and effective_bid(book) > effective_bid(best):
            best = book

    return best

def effective_ask(book):
    return book.asks[0].price * (Decimal(1) + book.taker_fee)

def best_seller(books):
    eligible_books = eligible_books_filter(books)
    if len(eligible_books) == 0:
        return None

    best = eligible_books[0]
    for book in eligible_books:
        if len(best.asks) == 0:
            best = book
        elif len(book.asks) > 0 and effective_ask(book) < effective_ask(best):
            best = book

    return best

# Trade is the return type of check_imbalance
Trade = namedtuple('Trade', ['pair', 'profit', 'quantity', 'bid_price', 'ask_price', 'trace', 'buyer', 'seller'])
def check_imbalance(buyer_book, seller_book, pair):

    buyer = get_exchange_handler(buyer_book.exchange_name)
    seller = get_exchange_handler(seller_book.exchange_name)
    bids = buyer_book.bids
    asks = seller_book.asks
    bids_idx = 0
    asks_idx = 0
    bid_price = bids[0].price
    ask_price = asks[0].price
    total_quantity = Decimal(0)
    total_profit = Decimal(0)

    # Only using 90% of balance in these calculations to leave wiggle room in case we need to do recovery and then the market moves
    max_notional = min(pair.max_notional(), seller.get_balance(pair.currency) * Decimal('0.9'))
    max_quantity = min(max_notional / bid_price, buyer.get_balance(pair.token) * Decimal('0.9'))

    trace = ""

    trace += "\n"
    trace += "best bid %0.8f @ %s\n" % (bids[0].price, buyer.name)
    trace += "best ask %0.8f @ %s\n" % (asks[0].price, seller.name)

    # update price array for NAV calculation
    if pair.currency == 'BTC' or (pair.currency == 'USDT' and pair.token == 'BTC') or (pair.currency == 'USD' and pair.token == 'BTC'):
        symbol = pair.token
        average_price = (bids[0].price + asks[0].price) / Decimal(2)
        if pair.currency == 'USDT' or pair.currency == 'USD': # our PRICE array is denominated in BTC so gotta flip USD(T) markets
            symbol = pair.currency
            average_price = Decimal(1) / average_price

        PRICE[symbol] = Decimal(average_price)
        price_collection.update({'symbol':symbol}, {'$set':{'price':float(average_price)}}, upsert=True)

    while(1):
        if DISABLE_TRADING:
            break

        if pair.token in ['']: # tokens temp. not trading
            break

        if buyer.name == seller.name:
            break

        if bids_idx >= len(bids) or asks_idx >= len(asks):
            break

        bid = bids[bids_idx]
        ask = asks[asks_idx]

        # not strictly necessary, but can help make the trace more readable
        if bid.price <= ask.price:
            break

        total_fee = buyer.get_fee(pair) + seller.get_fee(pair)
        friction = total_fee + Decimal('0.001') + pair.network_friction

        top_quantity = min(bid.quantity, ask.quantity, max_quantity - total_quantity)

        # if buyer.get_balance(pair.token) - total_quantity - top_quantity < seller.get_balance(pair.token) + total_quantity + top_quantity:
        #     friction_multiplier = Decimal(1) - ((buyer.get_balance(pair.token) - total_quantity - top_quantity) / (seller.get_balance(pair.token) + total_quantity + top_quantity))
        #     friction = friction + (friction_multiplier * pair.network_friction)

        benefit = bid.price - ask.price
        pct_benefit = benefit / bid.price
        trace += "benefit / friction / net : %0.8f / %0.8f / %0.8f\n" % (pct_benefit * Decimal(100), friction * Decimal(100), (pct_benefit - friction) * Decimal(100))

        if pct_benefit <= friction:
            break

        bid_price = bid.price
        ask_price = ask.price

        if top_quantity < bid.quantity and top_quantity < ask.quantity:
            total_quantity += top_quantity
            profit = (pct_benefit - friction) * ask.quantity * ask.price * Decimal(1000)
            total_profit += profit

            trace += "STACKING QTY %d/%d added: %0.8f, total: %0.8f\n" % (bids_idx, asks_idx, ask.quantity, total_quantity)
            trace += "STACKED PROFIT: %0.8f mBTC/mETH/mUSDT\n" % profit
            trace += "LIMITED ORDER SIZE DUE TO EXCHANGE BALANCE OR RISK CHECK\n"

            break

        elif bid.quantity > ask.quantity:
            total_quantity += ask.quantity
            bids[bids_idx] = Order(bid.price, bid.quantity - ask.quantity)
            profit = (pct_benefit - friction) * ask.quantity * ask.price * Decimal(1000)
            total_profit += profit

            trace += "STACKING QTY %d/%d added: %0.8f, total: %0.8f\n" % (bids_idx, asks_idx, ask.quantity, total_quantity)
            trace += "STACKED PROFIT: %0.8f mBTC/mETH/mUSDT\n" % profit

            asks_idx += 1

        else:
            total_quantity += bid.quantity
            asks[asks_idx] = Order(ask.price, ask.quantity - bid.quantity)
            profit = (pct_benefit - friction) * bid.quantity * bid.price * Decimal(1000)
            total_profit += profit

            trace += "STACKING QTY %d/%d added: %0.8f, total: %0.8f\n" % (bids_idx, asks_idx, bid.quantity, total_quantity)
            trace += "STACKED PROFIT: %0.8f mBTC/mETH/mUSDT\n" % profit

            bids_idx += 1

    # convert profit to mBTC before returning
    total_profit *= PRICE[pair.currency]

    trace += "ACTIONABLE IMBALANCE of %0.8f on %s WITH TOTAL PROFIT %0.8f\n" % (total_quantity, pair, total_profit)

    if total_quantity * ask_price < pair.min_notional():
        trace += "risk check MIN_NOTIONAL, skipping trade %0.8f\n" % (total_quantity * ask_price)
        total_profit = total_quantity = Decimal(0)

    if total_quantity < pair.min_quantity():
        trace += "risk check MIN_QTY, skipping trade %0.8f\n" % (total_quantity)
        total_profit = total_quantity = Decimal(0)

    return Trade(pair, total_profit, total_quantity, bid_price, ask_price, trace, buyer, seller)

def sanity_check_open(exch):
    if exch.protected_any_open_orders():
        record_event("SHUTDOWN,OPEN ORDERS,%s" % exch.name)
        sys.exit(1)

def sanity_check_max_autobalance(symbol, actual, target, pct_diff):
    if pct_diff > MAX_AUTOBALANCE:
        record_event("SHUTDOWN,MAX AUTOBALANCE,%s,%0.8f,%0.8f,%0.8f" % (symbol, actual, target, pct_diff))
        sys.exit(1)

def simulate_market_order(exch, book, amount):
    total_price = Decimal('0')
    final_price = Decimal('0')

    for order in book:
        if amount <= order.quantity:
            final_price = order.price
            total_price += amount * order.price
            amount = Decimal('0')
        else:
            final_price = order.price # will be overwritten
            total_price += order.quantity * order.price
            amount -= order.quantity

        if amount == Decimal('0'):
            break

    if amount > Decimal('0'):
        return (None, None, None)

    return (exch, total_price, final_price)

def sanity_check_market_price(price, top_of_book_price):
    pct_diff = abs(price - top_of_book_price) / top_of_book_price
    if pct_diff > Decimal(0.1):
        record_event("SANITY CHECK,MARKET PRICE")
        sys.exit(1)

def refresh_all_markets(pair, reason):
    books = query_pair(pair)

    invoke_all(books, reason)
    sleep(1, reason)
    invoke_all(books, reason)
    sleep(1, reason)
    invoke_all(books, reason)
    sleep(1, reason)

    return query_pair(pair)

def buy_at_market(reason, pair, _amount, expected_price=None):
    assert(DISABLE_TRADING == False)

    amount = _amount / Decimal('.9975') # buy enough to cover exchange fee

    record_event("MKT BUY,%s,%s,%s,%0.8f" % (reason, pair.token, pair.currency, amount))
    books = refresh_all_markets(pair, 'MKT BUY')

    if expected_price is None:
        expected_price = best_seller(books).asks[0].price

    books = eligible_books_filter(books)

    prices = map(lambda book: simulate_market_order(get_exchange_handler(book.exchange_name), book.asks, amount), books)
    eligible_prices = filter(lambda (exch, total, price):exch and exch.get_balance(pair.currency) > total, prices)

    if len(eligible_prices) == 0:
        record_event("MKT CANCEL,NONE ELIGIBLE")
        return Decimal(0)

    (best_exch, best_total, best_price) = min(eligible_prices, key=lambda (exch, total, price):total)

    # TODO it doesn't even work this way on like, bittrex, maybe others
    amount = _amount / (1 - best_exch.get_fee(pair)) # adjust amount; now that we know which exchange can use exact fee

    print "MKT BUY ROUTED to %s; %0.8f @ %0.8f, total: %0.8f" % (best_exch.name, amount, best_price, best_total)

    if not near_equals(best_price, expected_price, Decimal('0.1')):
        record_event("MKT CANCEL,PRICE CHANGE")
        return Decimal(0)

    # make trade
    if best_exch.trade_ioc(pair, 'buy', best_price, amount, reason) == Decimal(0):
        return None

    return best_exch

def sell_at_market(reason, pair, amount, expected_price=None):
    assert(DISABLE_TRADING == False)

    record_event("MKT SELL,%s,%s,%s,%0.8f" % (reason, pair.token, pair.currency, amount))
    books = refresh_all_markets(pair, 'MKT SELL')

    if expected_price is None:
        expected_price = best_bidder(books).bids[0].price

    books = eligible_books_filter(books)

    prices = map(lambda book: simulate_market_order(get_exchange_handler(book.exchange_name), book.bids, amount), books)
    eligible_prices = filter(lambda (exch, total, price):exch and exch.get_balance(pair.token) > amount, prices)

    if len(eligible_prices) == 0:
        record_event("MKT CANCEL,NONE ELIGIBLE")
        return Decimal(0)

    (best_exch, best_total, best_price) = max(eligible_prices, key=lambda (exch, total, price):total)

    print "MKT SELL ROUTED to %s; %0.8f @ %0.8f, total: %0.8f" % (best_exch.name, amount, best_price, best_total)

    if not near_equals(best_price, expected_price, Decimal('0.1')):
        record_event("MKT CANCEL,PRICE CHANGE")
        return Decimal(0)

    if best_exch.trade_ioc(pair, 'sell', best_price, amount, reason) == Decimal(0):
        return None

    return best_exch

# target is total target, targets is exchange-name mapped individual targets
def check_symbol_balance(symbol, target, targets):
    balance = total_balance(symbol)
    if balance < Decimal(1):
        return False

    tinfo = open_transfers_collection.find_one({'symbol':symbol, 'active':True})

    if balance < target and not near_equals(target, balance, BALANCE_ACCURACY):
        if not tinfo:
            if REPAIR_BALANCES and symbol not in ['BTC','ETH','USDT']:
                buy_at_market('REPAIR', pair_factory(symbol, 'BTC'), target-balance)
            else:
                record_event("WITHDRAW MISSING BALANCE,%s,%0.4f,%0.4f,%0.4f" % (symbol, target, balance, target-balance))
        else:
            # TODO highlight in transit, extra balance situation
            record_event("WITHDRAW IN TRANSIT,%s,%s,%s,%s,%s,%s" % (tinfo['from'], tinfo['to'], symbol, tinfo['amount'], tinfo['address'], tinfo['time']))
        return False

    elif balance > target or near_equals(target, balance, BALANCE_ACCURACY): # no pending transfers
        open_transfers_collection.update_many({'symbol':symbol}, {'$set':{'active':False}})
        if tinfo:
            record_event("WITHDRAW COMPLETED,%s,%s,%s,%s,%s,%s" % (tinfo['from'], tinfo['to'], symbol, tinfo['amount'], tinfo['address'], tinfo['time']))

        if not near_equals(target, balance, BALANCE_ACCURACY) and symbol not in ['BTC','ETH','USDT','USD']:
            if REPAIR_BALANCES:
                sell_at_market('REPAIR', pair_factory(symbol, 'BTC'), balance-target)
            else:
                record_event("WITHDRAW EXTRA BALANCE,%s,%0.4f,%0.4f,%0.4f" % (symbol, target, balance, balance-target))

        participating_exchanges = filter(lambda exch:symbol in exch.symbols and not exch.name in ['GDAX','ITBIT','BITFLYER'], exchanges)
        lowest_exchange = min(participating_exchanges, key=lambda exch:exch.balance[symbol] / targets[exch.name])
        highest_exchange = max(participating_exchanges, key=lambda exch:exch.balance[symbol] / targets[exch.name])
        if lowest_exchange.balance[symbol] / targets[lowest_exchange.name] < TRANSFER_THRESHOLD_LOW or \
           highest_exchange.balance[symbol] / targets[highest_exchange.name] > TRANSFER_THRESHOLD_HIGH:
            record_event("WITHDRAW_INFO,%s,%f,%f,%f,%f,%f,%f" % (symbol, highest_exchange.balance[symbol], targets[highest_exchange.name], highest_exchange.balance[symbol] - targets[highest_exchange.name] * DRAWDOWN_AMOUNT, lowest_exchange.balance[symbol], targets[lowest_exchange.name], targets[lowest_exchange.name] * DRAWUP_AMOUNT - lowest_exchange.balance[symbol]))
            transfer_amount = min(highest_exchange.balance[symbol] - targets[highest_exchange.name] * DRAWDOWN_AMOUNT,
                                  targets[lowest_exchange.name] * DRAWUP_AMOUNT - lowest_exchange.balance[symbol])

            if transfer_amount <= 0:
                record_event("SANITY CHECK,TRANSFER LOW")
                return False

            # make sure we don't transfer thrash
            if highest_exchange.balance[symbol] - transfer_amount <= targets[highest_exchange.name] * TRANSFER_THRESHOLD_LOW:
                record_event("SANITY CHECK,TRANSFER THRASH LOW")
                return False

            if lowest_exchange.balance[symbol] + transfer_amount >= targets[lowest_exchange.name] * TRANSFER_THRESHOLD_HIGH:
                record_event("SANITY CHECK,TRANSFER THRASH HIGH")
                return False

            amount_str = "%0.4f" % transfer_amount
            if symbol in ['NEO']:
                amount_str = "%0.0f" % transfer_amount
                if highest_exchange.name == 'BITTREX':
                    amount_str += ".025"

            record_event("WITHDRAW_ATTEMPT,%s,%s,%s,%s" % (highest_exchange.name, lowest_exchange.name, symbol, amount_str))

            if lowest_exchange.name == 'LIQUI' and exchange_nav_as_percentage_of_total(get_exchange_handler('LIQUI')) > LIQUI_NAV_PERCENTAGE_MAX:
                record_event("WITHDRAW_HOLD,%s,%0.3f" % (lowest_exchange.name, exchange_nav_as_percentage_of_total(get_exchange_handler('LIQUI'))))
            elif highest_exchange.active and lowest_exchange.active:
                timestamp = '{:%m-%d,%H:%M:%S}'.format(datetime.datetime.now())
                open_transfers_collection.insert_one({'symbol':symbol, 'amount':amount_str, 'address':lowest_exchange.deposit_address(symbol),
                    'from':highest_exchange.name, 'to':lowest_exchange.name, 'time':timestamp, 'active':True})

                highest_exchange.withdraw(lowest_exchange, symbol, amount_str)
                # force update balance for any exchanges with automated transfers
                if highest_exchange.name != 'LIQUI':
                    sleep(1, 'WITHDRAW_LOOP,BALANCE_REFRESH')
                    highest_exchange.unprotected_refresh_balances()
                return True
            else:
                record_event("WITHDRAW_SKIPPED,EXCHANGE_DOWN")
                return False

    return False

def check_symbol_balance_loop():
    record_event("WITHDRAW LOOP,***************************************************************")
    for symbol,targets in TARGET_BALANCE.items():
        try:
            check_symbol_balance(symbol, TOTAL_TARGET_BALANCE[symbol], targets)
        except:
            record_event("WITHDRAW_FAIL,%s" % symbol)
            sleep(1, 'WITHDRAW_LOOP')

def record_maker(title, record, order_info=None, (our_depth, covering_qty)=(None,None)):
    if order_info is None:
        vol_exec = "?"
    else:
        vol_exec = "%0.8f" % Decimal(order_info['vol_exec'])

    if our_depth is None:
        record_event("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s" % (title, record['at'], record['from'], record['pair'], record['side'], record['size'], vol_exec, record['vol_closed'], record['at_price'], record['from_price'], record['order_id']))
    else:
        record_event("%s,%s,%s,%s,%s,%d,%0.2f,%s,%s,%s,%s,%s,%s" % (title, record['at'], record['from'], record['pair'], record['side'], our_depth, covering_qty, record['size'], vol_exec, record['vol_closed'], record['at_price'], record['from_price'], record['order_id']))

# returns (n, qty), n is number of price levels above ours, qty is total qty at and above our price level
def find_our_order(book, our_price):
    total_quantity = 0

    for i in range(0, len(book)):
        total_quantity += book[i].quantity
        if book[i].price == our_price:
            return (i, total_quantity)

    return (99, total_quantity)

record_event('START')
print
print "Starting up"
print

make_at = get_exchange_handler('KRAKEN')
open_orders = list(maker_orders_collection.find({}))

# TODO if natural MAKER_MARKUP would cross book, increase to account for taker fee
MAKER_MARKUP = Decimal('0.0025')
MINIMUM_MARKUP = Decimal('0.0017')
MAXIMUM_MARKUP = Decimal('0.015')

for order in open_orders:
    record_maker('MAKER_OPEN', order)

for exch in exchanges:
    exch.initial_refresh_balances()
sleep(1, 'STARTUP,INITIAL_REFRESH')

#TODO cancel any orders at kraken not in our collection
for exch in exchanges:
    if exch.name != make_at.name:
        exch.protected_cancel_all_orders()
sleep(1, 'STARTUP,CANCEL_ALL')

for exch in exchanges:
    if exch.name != make_at.name:
        sanity_check_open(exch)
sleep(1, 'STARTUP,SANITY_CHECK_OPEN')

for exch in exchanges:
    exch.protected_refresh_balances()

MAKER_PAIR_LIST = [#pair_factory('ICN','BTC'), pair_factory('ICN','ETH'),
             pair_factory('REP','BTC'), pair_factory('REP','ETH'),
             pair_factory('GNO','BTC'), pair_factory('GNO','ETH'),
             pair_factory('MLN','BTC'),
             pair_factory('ZEC','BTC'),
             pair_factory('XRP','BTC'),
             pair_factory('XMR','BTC'),
             pair_factory('XLM','BTC')]
             # pair_factory('ETH','BTC'),
             # pair_factory('BCH','BTC'),
MAKER_SIZE = {'GNO':Decimal('3'), 'ICN':Decimal('350'), 'MLN':Decimal('4'), 'REP':Decimal('10'), 'ETH':Decimal('5'), 'BCH':Decimal('1'), 'LTC':Decimal('4'), 'XRP':Decimal('300'), 'XLM':Decimal('1500'), 'XMR':Decimal('2'), 'ZEC':Decimal('1')}
MAKER_MIN_CURRENCY_BALANCE = {'BTC':Decimal('0.4'), 'ETH':Decimal('5')}

while True:
    record_event("MAKER_HEARTBEAT,%s" % balances_string())

    need_bal_refresh = []

    open_orders = list(maker_orders_collection.find({}))
    order_infos = [] if len(open_orders) == 0 else make_at.order_infos(map(lambda o:o['order_id'], open_orders))

    all_books = query_all()
    need_books_refresh = False

    for pair in MAKER_PAIR_LIST:
        precision = make_at.price_decimals[str(pair)]
        size = MAKER_SIZE[pair.token]

        for side in ['buy','sell']:
            opp_side = 'sell' if side == 'buy' else 'buy'

            records = filter(lambda r:r['pair'] == str(pair) and r['side'] == side, open_orders)

            if need_books_refresh:
                all_books = query_all()
                need_books_refresh = False

            books = all_books[str(pair)]
            at_book = filter(lambda b:b.exchange_name == make_at.name, books)[0]

            order_size = MAKER_SIZE[pair.token] if len(records) == 0 else Decimal(records[0]['size']) - Decimal(records[0]['vol_closed'])

            from_book = None
            make_from = None
            from_price = None
            if side == 'buy':
                eligible_filter = lambda b:get_exchange_handler(b.exchange_name).get_balance(pair.token) >= order_size
                eligible_books = filter(lambda b:b.exchange_name != make_at.name and eligible_filter(b), books)
                if len(eligible_books):
                    prices = map(lambda book:(book, simulate_market_order(get_exchange_handler(book.exchange_name), book.bids, order_size)), eligible_books)
                    prices = filter(lambda (book, (exch, total, price)): exch is not None, prices)
                    if len(prices):
                        prices = map(lambda (book, (exch, total, price)): (book, exch, price * (Decimal(1) - exch.get_fee(pair))), prices)
                        (from_book, make_from, from_price) = max(prices, key=lambda (book, exch, price):price)
            else:
                eligible_filter = lambda b:get_exchange_handler(b.exchange_name).get_balance(pair.currency) > MAKER_MIN_CURRENCY_BALANCE[pair.currency]
                eligible_books = filter(lambda b:b.exchange_name != make_at.name and eligible_filter(b), books)
                if len(eligible_books):
                    prices = map(lambda book:(book, simulate_market_order(get_exchange_handler(book.exchange_name), book.asks, order_size)), eligible_books)
                    prices = filter(lambda (book, (exch, total, price)): exch is not None, prices)
                    if len(prices):
                        prices = map(lambda (book, (exch, total, price)): (book, exch, price * (Decimal(1) + exch.get_fee(pair))), prices)
                        (from_book, make_from, from_price) = min(prices, key=lambda (book, exch, price):price)

            if len(records) == 0:
                # TODO some sort of reserved balance logic?
                make_price = None

                if side == 'buy':
                    if make_from is None or make_from.get_balance(pair.token) < size:
                        record_event("MAKER_UNABLE_CREATE,%s,%s,%s" % (pair.token, pair.currency, side))
                    else:
                        print "Final price for selling %0.0f at %s: %0.8f" % (size, make_from.name, from_price)
                        make_price = from_price * (Decimal(1) - MAKER_MARKUP)
                        print "Unfixed Make market buy order at %s at: %0.8f" % (make_at.name, make_price)
                        make_price = make_price.quantize(Decimal(1)/Decimal(10**precision), rounding=ROUND_FLOOR)
                        print "Fixed Make market buy order at %s at: %0.8f" % (make_at.name, make_price)
                else:
                    assert(side == 'sell')
                    if make_from is None or make_from.get_balance(pair.currency) < MAKER_MIN_CURRENCY_BALANCE[pair.currency]:
                        record_event("MAKER_UNABLE_CREATE,%s,%s,%s" % (pair.token, pair.currency, side))
                    else:
                        print "Final price for buying %0.0f at %s: %0.8f" % (size, make_from.name, from_price)
                        make_price = from_price * (Decimal(1) + MAKER_MARKUP)
                        print "Unfixed Make market sell order at %s at: %0.8f" % (make_at.name, make_price)
                        make_price = make_price.quantize(Decimal(1)/Decimal(10**precision), rounding=ROUND_CEILING)
                        print "Fixed Make market sell order at %s at: %0.8f" % (make_at.name, make_price)

                if make_price:
                    print "Submitting %s order to %s for %0.8f at %0.8f" % (side, make_at.name, size, make_price)

                    order_return = make_at.query_private('AddOrder', {
                        'pair' : make_at.pair_name(pair),
                        'type' : side,
                        'ordertype' : 'limit',
                        'price' : ("%0." + str(make_at.price_decimals[str(pair)]) + "f") % make_price,
                        'volume' : ("%0." + str(make_at.lot_decimals[str(pair)]) + "f") % size,
                        'expiretm' : '+60'
                    })
                    print 'KRAKEN ORDER RETURN'
                    print order_return

                    if 'result' in order_return:
                        txid = order_return['result']['txid'][0]

                        record = {
                            'at' : make_at.name,
                            'from' : make_from.name,
                            'pair' : str(pair),
                            'side' : side,
                            'size' : "%0.8f" % size,
                            'vol_closed' : '0',
                            'at_price' : "%0.8f" % make_price,
                            'from_price' : "%0.8f" % from_price,
                            'order_id' : txid
                        }

                        record_maker("MAKER_CREATE", record)
                        maker_orders_collection.insert_one(record)
                        need_books_refresh = True
                    else:
                        err_message = order_return['error'] if error in order_return else ''
                        record_event("MAKER_CREATE_FAIL,%s,%s,%s" % (pair.token, pair.currency, err_message))
            else:
                assert(len(records) == 1)
                record = records[0]
                order_id = record['order_id']
                print "Reviewing active %s order on %s, id: %s" % (side, str(pair), order_id)
                print record
                print
                order_info = order_infos[order_id]
                print order_info

                at_book_side = at_book.bids if side == 'buy' else at_book.asks

                record_maker("MAKER_REVIEW", record, order_info, find_our_order(at_book_side, Decimal(order_info['descr']['price'])))

                vol_closed = Decimal(record['vol_closed'])
                if Decimal(order_info['vol_exec']) - vol_closed > pair.min_quantity():
                    market_price = from_price * (Decimal(1.01) if opp_side == 'buy' else Decimal(0.99))
                    closed_amount = make_from.trade_ioc(pair, opp_side, market_price, Decimal(order_info['vol_exec']) - vol_closed, 'MAKER_CLOSEOUT')
                    vol_closed = vol_closed + closed_amount
                    record['vol_closed'] = "%0.8f" % vol_closed
                    maker_orders_collection.update({'order_id':record['order_id']}, {'$set':{'vol_closed':record['vol_closed']}})
                    need_bal_refresh += [make_from]
                    need_books_refresh = True
                    record_trade("MAKER,%s,%s,%s,%s,%s,%0.4f,%0.4f" % (make_from.name, make_at.name, side.upper(), pair.token, pair.currency, closed_amount, vol_closed))

                print "Total Closed qty: %0.8f" % vol_closed

                if Decimal(order_info['vol_exec']) - vol_closed > pair.min_quantity():
                    print "UNABLE TO CLOSE THE FILL???"
                    record_maker('MAKER_UNABLE_CLOSE_FILL', record, order_info)

                def do_cancel():
                    make_at.cancel(order_id)
                    need_books_refresh = True

                if not (order_info['status'] == 'pending' or order_info['status'] == 'open'):
                    record_maker("MAKER_DONE", record, order_info)
                    maker_orders_collection.delete_many({'order_id':order_id})
                else:
                    if vol_closed > Decimal('0.8') * MAKER_SIZE[pair.token]:
                        record_maker("MAKER_CANCEL_MOSTLY_FILLED", record, order_info)
                        do_cancel()

                    if from_price is None:
                        record_maker("MAKER_CANCEL_NO_FROM", record, order_info)
                        do_cancel()
                    else:
                        if opp_side == 'buy':
                            if make_at.get_balance(pair.currency) < MAKER_MIN_CURRENCY_BALANCE[pair.currency]:
                                record_maker("MAKER_CANCEL_LOW_CURRENCY_BALANCE", record, order_info)
                                do_cancel()
                            elif from_price * (Decimal(1) + MINIMUM_MARKUP) > Decimal(record['at_price']):
                                record_maker("MAKER_CANCEL_LOW_MARKUP", record, order_info)
                                do_cancel()
                            elif from_price * (Decimal(1) + MAXIMUM_MARKUP) < Decimal(record['at_price']):
                                record_maker("MAKER_CANCEL_HIGH_MARKUP", record, order_info)
                                do_cancel()
                        else:
                            assert(opp_side == 'sell')
                            if make_at.get_balance(pair.token) < MAKER_SIZE[pair.token]:
                                record_maker("MAKER_CANCEL_LOW_TOKEN_BALANCE", record, order_info)
                                do_cancel()
                            elif from_price * (Decimal(1) - MINIMUM_MARKUP) < Decimal(record['at_price']):
                                record_maker("MAKER_CANCEL_LOW_MARKUP", record, order_info)
                                do_cancel()
                            elif from_price * (Decimal(1) - MAXIMUM_MARKUP) > Decimal(record['at_price']):
                                record_maker("MAKER_CANCEL_HIGH_MARKUP", record, order_info)
                                do_cancel()

    if need_bal_refresh:
        for exch in need_bal_refresh:
            exch.refresh_balances()
        make_at.refresh_balances()

    sleep(1, 'MAKER_LOOP')

# while True:
#     order_info = make_at.order_info(txid)
#     filled_qty = Decimal(order_info['vol_exec'])
#     print "Filled qty: %0.8f" % filled_qty
#
#     if filled_qty - total_closed > pair.min_quantity():
#         closed_amount = make_from.trade_ioc(pair, 'buy', final_price * Decimal(1.1), filled_qty - total_closed, 'MAKER_CLOSEOUT')
#         total_closed = total_closed + closed_amount
#     print "Total Closed qty: %0.8f" % total_closed
#
#     if filled_qty - total_closed > pair.min_quantity():
#         print "Unable to close the fill???"
#         sys.exit(1)
#
#     books = query_pair(pair)
#     from_book = filter(lambda b:b.exchange_name == make_from.name, books)[0]
#     (unused, unused, final_price) = simulate_market_order(make_from, from_book.asks, size - filled_qty)
#
#     if final_price * (Decimal(1) + MINIMUM_MARKUP) > make_price:
#         print "Market moved, time to cancel"
#         make_at.cancel(txid)
#         time.sleep(2)
#         order_info = make_at.order_info(txid)
#
#     if not (order_info['status'] == 'pending' or order_info['status'] == 'open'):
#         print "Order is closed, shutting down"
#         break
#
#     print "sleeping"
#     print
#     time.sleep(2)
#
# for exch in exchanges:
#     exch.protected_refresh_balances()
#
# record_event("MAKERCLOSEOUT_HEARTBEAT,%s" % balances_string())
#
# print "Done Cleanly"

# print
#
# (unused, unused, final_price) = simulate_market_order(binance, binance_book.bids, size)
#
# print "Final price for selling %0.0f at %s: %0.8f" % (size, make_from.name, final_price)
#
# make_price = final_price * (Decimal(1) - MAKER_MARKUP)
# print "Unfixed Make market buy order at %s at: %0.8f" % (make_at.name, make_price)
#
# make_price = make_price.quantize(Decimal(1)/Decimal(10**precision), rounding=ROUND_FLOOR)
# print "Fixed Make market buy order at %s at: %0.8f" % (make_at.name, make_price)

#
# while open_trades_collection.find_one():
#     trade = open_trades_collection.find_one()
#
#     if trade['recovery_attempts'] > MAX_RECOVERY_ATTEMPTS:
#         record_event("CANCELLING RECOVERY,MAX ATTEMPTS")
#         open_trades_collection.delete_one({'_id':trade['_id']})
#         break
#     else:
#         open_trades_collection.update({'_id':trade['_id']}, {'$set':{'recovery_attempts':trade['recovery_attempts']+1}})
#
#     for exch in exchanges:
#         # we must get fresh balances from the exchanges involved in the recovery
#         if exch.name == trade['buyer'] or exch.name == trade['seller']:
#             exch.unprotected_refresh_balances()
#         else:
#             exch.protected_refresh_balances()
#
#     sleep(1, 'RECOVERY,REFRESH_BALANCES')
#
#     print balances_string()
#     print balances_detail()
#
#     pair = pair_factory(trade['token'], trade['currency'])
#     balance = total_balance(pair.token)
#
#     record_event("RECOVERY BEGIN,%d,%s,%s,%s,%s,%s,%s,%s,%s" % (trade['recovery_attempts'], trade['buyer'], trade['seller'], trade['token'], trade['currency'], balance, trade['token_balance'], trade['bid'], trade['ask']))
#     target_balance = Decimal(trade['token_balance'])
#
#     if abs(target_balance - balance) * Decimal(.98) > Decimal(trade['quantity']):
#         record_event("SKIPPING RECOVERY,DISCREPENCY")
#         open_trades_collection.delete_one({'_id':trade['_id']})
#         break
#
#     if abs(target_balance - balance) < pair.min_quantity():
#         record_event("SKIPPING RECOVERY,MIN_QTY")
#         open_trades_collection.delete_one({'_id':trade['_id']})
#         break
#
#     if balance > target_balance:
#         if (balance - target_balance) * Decimal(trade['bid']) < pair.min_notional():
#             record_event("SKIPPING RECOVERY,MIN_NOTIONAL")
#             open_trades_collection.delete_one({'_id':trade['_id']})
#         else:
#             traded_exchange = sell_at_market("RECOVERY AUTOBALANCE", pair, balance - target_balance, Decimal(trade['bid']))
#             if traded_exchange is None:
#                 record_event("SKIPPING RECOVERY,ZERO FILL")
#                 open_trades_collection.delete_one({'_id':trade['_id']})
#             else:
#                 sleep(2, 'RECOVERY,BALANCE_REFRESH')
#                 traded_exchange.unprotected_refresh_balances()
#                 sleep(1, 'RECOVERY,BALANCE_REFRESH')
#     else:
#         if (target_balance - balance) * Decimal(trade['ask']) < pair.min_notional():
#             record_event("SKIPPING RECOVERY,MIN_NOTIONAL")
#             open_trades_collection.delete_one({'_id':trade['_id']})
#         else:
#             traded_exchange = buy_at_market("RECOVERY AUTOBALANCE", pair, target_balance - balance, Decimal(trade['ask']))
#             if traded_exchange is None:
#                 record_event("SKIPPING RECOVERY,ZERO FILL")
#                 open_trades_collection.delete_one({'_id':trade['_id']})
#             else:
#                 sleep(2, 'RECOVERY,BALANCE_REFRESH')
#                 traded_exchange.unprotected_refresh_balances()
#                 sleep(1, 'RECOVERY,BALANCE_REFRESH')
#
#     sleep(2, 'RECOVERY,LOOP_CLOSE')
#
#
# for exch in exchanges:
#     exch.protected_refresh_balances()
#
# last_balance_check_time = 0
#
# while True:
#     print
#     print balances_string()
#     print balances_detail()
#
#     record_event("CONFIRMED,%s" % balances_string_confirmed())
#     record_event("DETAIL,%s" % balances_detail())
#     record_event("BTCVALUE,%s" % balances_string_in_btc())
#     record_event("HEARTBEAT,%s" % balances_string())
#
#     if arbitrage_revenue() < Decimal(-10):
#         record_event("RISK_CHECK,PANIC! AT THE DISCO")
#         sys.exit(1)
#
#     if last_balance_check_time + 300 < int(time.time()):
#         check_symbol_balance_loop()
#         last_balance_check_time = int(time.time())
#
#     if REPAIR_BALANCES:
#         sys.exit(1)
#
#     best_trade = None
#     for pair, pair_books in query_all().iteritems():
#         (token, currency) = pair.split('-')
#         pair = pair_factory(token, currency)
#         if pair is None:
#             continue
#
#         buyer = best_bidder(pair_books)
#         seller = best_seller(pair_books)
#         if buyer is None or seller is None:
#             continue
#
#         trade = check_imbalance(buyer, seller, pair)
#         if pair.token == 'ICN' and pair.currency == 'BTC':
#             print trade.trace
#         if trade.profit > 0 and (best_trade is None or best_trade.profit < trade.profit):
#             best_trade = trade
#
#     if best_trade is None:
#         if DISABLE_TRADING:
#             sleep(60, 'NO_TRADING')
#             for exch in exchanges:
#                 exch.protected_refresh_balances()
#         else:
#             sleep(2, 'NO_TRADE')
#     else:
#         print best_trade.trace
#         record_event("TRADE,%s,%s,%s,%.8f,%.8f,%.8f,%.8f" %
#             (best_trade.pair, best_trade.buyer.name, best_trade.seller.name,
#              best_trade.profit, best_trade.quantity, best_trade.bid_price, best_trade.ask_price))
#
#         execute_trade(best_trade.buyer, best_trade.seller, best_trade.pair, best_trade.quantity, best_trade.profit, best_trade.bid_price, best_trade.ask_price)
#
#         sleep(8, 'TRADED')
#
#         for exch in exchanges:
#             exch.protected_refresh_balances()
