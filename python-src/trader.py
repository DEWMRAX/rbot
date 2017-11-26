import datetime, sys, time
from collections import namedtuple
from decimal import Decimal
from pymongo import MongoClient

import poloniex, bittrex, binance, liqui
from book import query_all
from logger import record_event, record_trade
from order import Order
from pair import ALL_PAIRS, ALL_SYMBOLS, pair_factory

MAX_BOOK_AGE = 8
TRANSFER_THRESHOLD=Decimal('.25')
DRAWDOWN_AMOUNT=Decimal('.70') # how much to leave on an exchange we are withdrawing from
DRAWUP_AMOUNT=Decimal('1.4') # how much to target on an exchange we are transferring to

UPDATE_TARGET_BALANCE=False

if len(sys.argv) > 1:
    if sys.argv[1] == 'zero_balances':
        UPDATE_TARGET_BALANCE=True

open_trades_collection = MongoClient().arbot.trades
open_transfers_collection = MongoClient().arbot.transfers
target_balance_collection = MongoClient().arbot.targets
price_collection = MongoClient().arbot.prices

def panic(response):
    print response.status
    print response.error
    print response
    print "PANIC! At The Disco"
    sys.exit(1)

 # order determines execution ordering, assumes more liquidity at the latter exchange
 #   and that earlier exchanges are faster responding
exchanges = [liqui.Liqui(), binance.Binance(), bittrex.Bittrex(), poloniex.Poloniex()]
def get_exchange_handler(name):
    return filter(lambda exchange:exchange.name == name, exchanges)[0]

PRICE = {'BTC' : Decimal(1)}
for record in price_collection.find({}):
    PRICE[record['symbol']] = Decimal(record['price'])

def near_equals(x, y, threshold='0.001'):
    return (abs(x - y) / x) < Decimal(threshold)

def get_exchanges(pair):
    return filter(lambda exch:exch.has_pair(pair), exchanges)

def total_balance(symbol):
    return sum(map(lambda exch:exch.get_balance(symbol), exchanges))

TARGET_BALANCE = dict()
for symbol in ALL_SYMBOLS:
    doc = target_balance_collection.find_one({'symbol':symbol})
    TARGET_BALANCE[symbol] = Decimal(doc['balance'] if doc else 0)

def total_balance_incl_pending(symbol):
    confirmed = total_balance(symbol)
    target = TARGET_BALANCE[symbol]

    if confirmed > target or near_equals(confirmed, target, '0.05'):
        return confirmed

    transfer = open_transfers_collection.find_one({'symbol':symbol, 'active':True})
    if transfer:
        return confirmed + Decimal(transfer['amount'])

    return confirmed

if UPDATE_TARGET_BALANCE:
    for exch in exchanges:
        exch.refresh_balances()

    for symbol in ALL_SYMBOLS:
        balance = "%0.8f" % total_balance_incl_pending(symbol)
        target_balance_collection.update({'symbol':symbol}, {'$set':{'balance':balance}}, upsert=True)

    sys.exit(0)
    time.sleep(3) # don't forget to throttle if decide not to shut down after

def target_nav():
    return sum(map(lambda symbol: PRICE[symbol]*TARGET_BALANCE[symbol], ALL_SYMBOLS))

def balances_nav(balance_func):
    return sum(map(lambda symbol: PRICE[symbol]*balance_func(symbol), ALL_SYMBOLS))

def balances_string_helper(balance_func):
    nav = balances_nav(balance_func)
    return ("%0.4f,%0.8f," % (1000*(nav-target_nav()), nav)) + ','.join(map(lambda symbol: "%0.8f" % balance_func(symbol), ALL_SYMBOLS))

def balances_string_in_btc():
    nav = balances_nav(total_balance_incl_pending)
    return ("%0.4f,%0.8f," % (1000*(nav-target_nav()), nav)) + ','.join(map(lambda symbol: "%0.8f" % (PRICE[symbol] * total_balance_incl_pending(symbol)), ALL_SYMBOLS))

def balances_string():
    return balances_string_helper(total_balance_incl_pending)

def balances_string_confirmed():
    return balances_string_helper(total_balance)

def balances_detail():
    return ','.join(map(lambda exch:','.join(map(lambda symbol: "%0.8f" % exch.get_balance(symbol), ALL_SYMBOLS)), exchanges))

def execute_trade(buyer, seller, pair, quantity, expected_profit, bid, ask):

    starting_currency_balance = total_balance(pair.currency)
    starting_token_balance = total_balance(pair.token)

    trade_doc = {'buyer':buyer.name, 'seller':seller.name, 'quantity':"%0.8f" % quantity,
                 'token':pair.token, 'currency':pair.currency, 'bid':"%0.8f" % bid, 'ask':"%0.8f" % ask,
                 'token_balance':"%0.8f" % starting_token_balance}
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

    time.sleep(2) # give exchanges (bittrex) chance to update balances
    buyer.refresh_balances()
    seller.refresh_balances()

    ending_currency_balance = total_balance(pair.currency)
    actual_profit = (ending_currency_balance - starting_currency_balance) * Decimal(1000) * PRICE[pair.currency]

    exec_report = info + ",%0.8f,%0.8f\n" % (quantity, actual_profit)

    record_trade(exec_report)

    info = balances_string() + ",%s,%s,%s,%s,%0.8f,%0.8f,%0.8f,%0.8f" % (buyer.name, seller.name, pair.token, pair.currency, quantity, bid, ask, expected_profit * Decimal(1000))

    record_event("AI_CLOSE,%s" % info)

def eligible_books_filter(books):
    return filter(lambda book:book.age < MAX_BOOK_AGE and book.exchange_name not in ['KRAKEN'], books)

def best_bidder(books):
    eligible_books = eligible_books_filter(books)
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
    eligible_books = eligible_books_filter(books)
    if len(eligible_books) == 0:
        return None

    best = eligible_books[0]
    for book in eligible_books:
        if len(best.asks) == 0:
            best = book
        elif len(book.asks) > 0 and book.asks[0].price < best.asks[0].price:
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
    if pair.currency == 'BTC' or (pair.currency == 'USDT' and pair.token == 'BTC'):
        symbol = pair.token
        average_price = (bids[0].price + asks[0].price) / Decimal(2)
        if pair.currency == 'USDT': # our NAV is denominated in BTC so gotta flip USDT markets
            symbol = 'USDT'
            average_price = Decimal(1) / average_price

        PRICE[symbol] = Decimal(average_price)
        price_collection.update({'symbol':symbol}, {'$set':{'price':float(average_price)}}, upsert=True)

    while(1):
        if bids_idx >= len(bids) or asks_idx >= len(asks):
            break

        bid = bids[bids_idx]
        ask = asks[asks_idx]

        # not strictly necessary, but can help make the trace more readable
        if bid.price <= ask.price:
            break

        total_fee = buyer.get_fee(pair) + seller.get_fee(pair)
        friction = total_fee + Decimal('0.002')

        top_quantity = min(bid.quantity, ask.quantity, max_quantity - total_quantity)

        if buyer.get_balance(pair.token) - total_quantity - top_quantity < seller.get_balance(pair.token) + total_quantity + top_quantity:
            friction_multiplier = Decimal(1) - ((buyer.get_balance(pair.token) - total_quantity - top_quantity) / (seller.get_balance(pair.token) + total_quantity + top_quantity))
            friction = friction + (friction_multiplier * pair.network_friction)

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
    if exch.any_open_orders():
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

def buy_at_market(reason, pair, amount, expected_price):
    amount = amount / Decimal('.9975') # buy enough to cover exchange fee

    record_event("MKT BUY,%s,%s,%s,%0.8f" % (reason, pair.token, pair.currency, amount))

    prices = map(lambda exch: simulate_market_order(exch, exch.asks[str(pair)], amount), get_exchanges(pair))

    eligible_prices = filter(lambda (exch, total, price):exch and exch.get_balance(pair.currency) > total, prices)
    if len(eligible_prices) == 0:
        record_event("MKT CANCEL,NONE ELIGIBLE")
        return Decimal(0)

    (best_exch, best_total, best_price) = min(eligible_prices, key=lambda (exch, total, price):total)

    amount = amount / (1 - best_exch.get_fee(pair)) # adjust amount; now that we know which exchange can use exact fee

    print "MKT BUY ROUTED to %s; %0.8f @ %0.8f, total: %0.8f" % (best_exch.name, amount, best_price, best_total)

    if not USE_TARGET_BALANCE:
        if not near_equals(best_price, expected_price, Decimal('0.1')):
            record_event("MKT CANCEL,PRICE CHANGE")
            return Decimal(0)

    sanity_check_market_price(best_price, best_exch.asks[str(pair)][0].price)

    return best_exch.trade_ioc(pair, 'buy', best_price, amount, reason)

def sell_at_market(reason, pair, amount, expected_price):

    record_event("MKT SELL,%s,%s,%s,%0.8f" % (reason, pair.token, pair.currency, amount))

    prices = map(lambda exch: simulate_market_order(exch, exch.bids[str(pair)], amount), get_exchanges(pair))

    eligible_prices = filter(lambda (exch, total, price):exch and exch.get_balance(pair.token) >= amount, prices)
    if len(eligible_prices) == 0:
        record_event("MKT CANCEL,NONE ELIGIBLE")
        return Decimal(0)

    (best_exch, best_total, best_price) = max(eligible_prices, key=lambda (exch, total, price):total)

    print "MKT SELL ROUTED to %s; %0.8f @ %0.8f, total: %0.8f" % (best_exch.name, amount, best_price, best_total)

    if not USE_TARGET_BALANCE:
        if not near_equals(best_price, expected_price, Decimal('0.1')):
            record_event("MKT CANCEL,PRICE CHANGE")
            return Decimal(0)

    sanity_check_market_price(best_price, best_exch.bids[str(pair)][0].price)

    return best_exch.trade_ioc(pair, 'sell', best_price, amount, reason)

def check_symbol_balance(symbol, target):
    balance = total_balance(symbol)

    if balance < target and not near_equals(target, balance, '0.05'):
        tinfo = open_transfers_collection.find_one({'symbol':symbol, 'active':True})
        if not tinfo:
            record_event("WITHDRAW MISSING BALANCE,%s,%0.4f,%0.4f,%0.4f" % (symbol, target, balance, target-balance))
        else:
            record_event("WITHDRAW IN TRANSIT,%s,%s,%s,%s,%s,%s" % (tinfo['from'], tinfo['to'], symbol, tinfo['amount'], tinfo['address'], tinfo['time']))
        return False

    elif balance > target or near_equals(target, balance, '0.05'): # no pending transfers
        open_transfers_collection.update_many({'symbol':symbol}, {'$set':{'active':False}})

        if not near_equals(target, balance, '0.05') and symbol not in ['BTC','ETH','USDT']:
            record_event("WITHDRAW EXTRA BALANCE,%s,%0.4f,%0.4f,%0.4f" % (symbol, target, balance, balance-target))

        participating_exchanges = filter(lambda exch:symbol in exch.symbols, exchanges)
        exchange_count = len(participating_exchanges)
        lowest_exchange = min(participating_exchanges, key=lambda exch:exch.balance[symbol]) # intentionally using unsafe get_balance
        highest_exchange = max(participating_exchanges, key=lambda exch:exch.balance[symbol])

        exchange_target = balance / exchange_count
        if lowest_exchange.balance[symbol] < exchange_target * TRANSFER_THRESHOLD:
            transfer_amount = min(highest_exchange.balance[symbol] - exchange_target * DRAWDOWN_AMOUNT,
                                  exchange_target * DRAWUP_AMOUNT - lowest_exchange.balance[symbol])
            if transfer_amount <= 0:
                record_event("SANITY CHECK,TRANSFER LOW")
                return False

            # make sure we don't transfer thrash
            if highest_exchange.balance[symbol] - transfer_amount <= exchange_target * TRANSFER_THRESHOLD:
                record_event("SANITY CHECK,TRANSFER THRASH")
                return False

            amount_str = "%0.4f" % transfer_amount
            record_event("WITHDRAW_ATTEMPT,%s,%s,%s,%s" % (highest_exchange.name, lowest_exchange.name, symbol, amount_str))
            highest_exchange.withdraw(lowest_exchange, symbol, amount_str)
            timestamp = '{:%m-%d,%H:%M:%S}'.format(datetime.datetime.now())
            open_transfers_collection.insert_one({'symbol':symbol, 'amount':amount_str, 'address':lowest_exchange.deposit_address(symbol),
                'from':highest_exchange.name, 'to':lowest_exchange.name, 'time':timestamp, 'active':True})
            return True

    return False

def check_symbol_balance_loop(balance_map):
    record_event("WITHDRAW LOOP")
    for symbol,target in balance_map.items():
        try:
            if check_symbol_balance(symbol, target):
                time.sleep(2)
        except:
            record_event("WITHDRAW_FAIL,%s" % symbol)
            time.sleep(2)
    for exch in exchanges:
        exch.refresh_balances()

record_event('START')
print
print "Starting up"
print

for exch in exchanges:
    exch.cancel_all_orders()

time.sleep(1)

for exch in exchanges:
    exch.refresh_balances()

time.sleep(1)

for exch in exchanges:
    sanity_check_open(exch)

print balances_string()
print balances_detail()

while open_trades_collection.find_one():
    trade = open_trades_collection.find_one()

    record_event("RECOVERY_NEEDED,%s,%s,%s,%s,%s,%s,%s,%s" % (trade['buyer'], trade['seller'], trade['token'], trade['currency'], balance, trade['token_balance'], trade['bid'], trade['ask']))
    sys.exit(1)

    pair = pair_factory(trade['token'], trade['currency'])
    balance = total_balance(pair.token)

    record_event("RECOVERY BEGIN,%s,%s,%s,%s,%s,%s,%s,%s" % (trade['buyer'], trade['seller'], trade['token'], trade['currency'], balance, trade['token_balance'], trade['bid'], trade['ask']))

    target_balance = Decimal(trade['token_balance'])

    if abs(target_balance - balance) * Decimal(.98) > Decimal(trade['quantity']):
        record_event("SKIPPING RECOVERY,DISCREPENCY")
        open_trades_collection.delete_one({'_id':trade['_id']})
        break

    if abs(target_balance - balance) < pair.min_quantity():
        record_event("SKIPPING RECOVERY,MIN_QTY")
        open_trades_collection.delete_one({'_id':trade['_id']})
        break

    record_event("SHUTDOWN,RECOVERY_NEEDED,%s,%s" % (pair, balance - target_balance))

    if balance > target_balance:
        if (balance - target_balance) * Decimal(trade['bid']) < pair.min_notional():
            record_event("SKIPPING RECOVERY,MIN_NOTIONAL")
            open_trades_collection.delete_one({'_id':trade['_id']})
        elif sell_at_market("RECOVERY AUTOBALANCE", pair, balance - target_balance, Decimal(trade['bid'])) == Decimal(0):
            record_event("SKIPPING RECOVERY,ZERO FILL")
            open_trades_collection.delete_one({'_id':trade['_id']})
    else:
        if (target_balance - balance) * Decimal(trade['ask']) < pair.min_notional():
            record_event("SKIPPING RECOVERY,MIN_NOTIONAL")
            open_trades_collection.delete_one({'_id':trade['_id']})
        elif buy_at_market("RECOVERY AUTOBALANCE", pair, target_balance - balance, Decimal(trade['ask'])) == Decimal(0):
            record_event("SKIPPING RECOVERY,ZERO FILL")
            open_trades_collection.delete_one({'_id':trade['_id']})

    time.sleep(1)

    for exch in get_exchanges(pair):
        exch.refresh_balances()

    time.sleep(1)

last_balance_check_time = 0

while True:
    print
    print balances_string()
    print balances_detail()

    record_event("CONFIRMED,%s" % balances_string_confirmed())
    record_event("DETAIL,%s" % balances_detail())
    record_event("BTCVALUE,%s" % balances_string_in_btc())
    record_event("HEARTBEAT,%s" % balances_string())

    if last_balance_check_time + 60 < int(time.time()):
        check_symbol_balance_loop(TARGET_BALANCE)
        last_balance_check_time = int(time.time())

    best_trade = None
    for pair, pair_books in query_all().iteritems():
        (token, currency) = pair.split('-')
        pair = pair_factory(token, currency)
        if pair is None:
            continue

        buyer = best_bidder(pair_books)
        seller = best_seller(pair_books)
        if buyer is None or seller is None:
            continue

        trade = check_imbalance(buyer, seller, pair)
        if trade.profit > 0 and (best_trade is None or best_trade.profit < trade.profit):
            best_trade = trade

    if best_trade is None:
        record_event("NO_TRADE")
        record_event("SLEEPING,1")
        time.sleep(1)
    else:
        print best_trade.trace
        record_event("TRADE,%s,%s,%s,%.8f,%.8f,%.8f,%.8f" %
            (best_trade.pair, best_trade.buyer.name, best_trade.seller.name,
             best_trade.profit, best_trade.quantity, best_trade.bid_price, best_trade.ask_price))

        execute_trade(best_trade.buyer, best_trade.seller, best_trade.pair, best_trade.quantity, best_trade.profit, best_trade.bid_price, best_trade.ask_price)

        record_event("SLEEPING,15")
        time.sleep(15)

        for exch in exchanges:
            exch.refresh_balances()
