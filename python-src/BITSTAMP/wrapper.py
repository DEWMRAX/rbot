from decimal import *
from exchange import Exchange
from order import Order
from logger import record_event
from fees import FEES
import json
import time

import bitstamp.client

def symbol_from_bitstamp(symbol):
    if symbol == 'bch':
        return 'BCC'
    else:
        return symbol.upper()

def symbol_to_bitstamp(symbol):
    if symbol == 'BCC':
        return 'bch'
    else:
        return symbol.lower()

PAIRS = dict()
INFO_CACHE_PATH = 'bitstamp_info.json'
CLOSED_STATES = ['Canceled', 'Finished']

with open(INFO_CACHE_PATH) as f:
    info = json.loads(f.read())
    for pair_info in info:
        token = symbol_from_bitstamp(pair_info['url_symbol'][0:3])
        currency = symbol_from_bitstamp(pair_info['url_symbol'][3:6])

        PAIRS["%s-%s" % (token, currency)] = {
            'price_decimals' : pair_info['counter_decimals'],
            'lot_decimals' : pair_info['base_decimals'],
            'token' : token,
            'currency' : currency
        }

class BITSTAMP(Exchange):
    def __init__(self):
        Exchange.__init__(self, 'BITSTAMP')
        with open('bitstamp.keys') as secrets_file:
            secrets = json.load(secrets_file)

            self.api = bitstamp.client.Trading(username=secrets['username'], key=secrets['key'], secret=secrets['secret'])

        self.symbols = ['USD','BTC','ETH','LTC','BCC','XRP']

        for ticker,info in PAIRS.iteritems():
            if info['token'] in self.symbols and info['currency'] in self.symbols:
                # TODO can pull fees from account info call
                self.fees[ticker] = FEES[self.name].taker

    def pair_name(self, pair):
        return "%s%s" % (symbol_to_bitstamp(pair.token), symbol_to_bitstamp(pair.currency))

    def deposit_address(self, symbol):
        addr_map = {
            'BTC':'3QMypupHax8pk5MvwvJBMfe8NMqYrbAHdG',
            'LTC':'MCy2iNhnVyLDoL5JqBGUxajqcPbjQeDyCM',
            'ETH':'0x504d9d5a9933840d4cf38024e088aefad00caffa',
            'BCC':'33x3CiR7qPkmresKhr7mchYELTu9szRh2x',
            'XRP':'rDsbeomae4FXwgQTJp9Rs64Qg9vDiTCdBv',
            'USD':'SILVERGATE'
        }

        return addr_map[symbol]

    def deposit_message(self, symbol):
        msg_map = {
            "XRP":"92261687"
        }
        return msg_map[symbol]

    def withdraw(self, dest, symbol, amount):
        # TODO DO NOT AUTOMATE ETHER WITHDRAWALS!!!
        address = dest.deposit_address(symbol)
        message = ''
        event = "WITHDRAW,%s,%s,%s,%s,%s" % (self.name, dest.name, symbol, amount, address)
        if symbol in self.require_deposit_message:
            event += ',' + dest.deposit_message(symbol)

        record_event(event)

    def refresh_balances(self):
        balance_info = self.api.account_balance(base=None, quote=None)
        for symbol in self.symbols:
            self.balance[symbol] = Decimal(balance_info["%s_balance" % symbol_to_bitstamp(symbol)])

    def any_open_orders(self):
        return len(self.api.open_orders(base="all/", quote="")) > 0

    def cancel_all_orders(self):
        self.api.cancel_all_orders()

    def place_limit_order(self, pair, side, price, amount):
        price = ("%0." + str(PAIRS[str(pair)]['price_decimals']) + "f") % price
        amount = ("%0." + str(PAIRS[str(pair)]['lot_decimals']) + "f") % amount

        data = {'amount': amount, 'price': price, 'ioc_order': True}

        url = self.api._construct_url(side + "/", symbol_to_bitstamp(pair.token), symbol_to_bitstamp(pair.currency))
        return self.api._post(url, data=data, return_json=True, version=2)

    def order_status(self, order_id):
        try:
            data = {'id': order_id}
            return self.api._post("order_status/", data=data, return_json=True, version=2)
        except:
            return {'status':'unknown'}

    def trade_ioc(self, pair, side, price, amount, reason):
        order_id = self.place_limit_order(pair, side, price, amount)['id']
        print 'order id'
        print order_id

        order_info = self.order_status(order_id)

        print 'first print'
        print order_info

        if order_info['status'] not in CLOSED_STATES:
            record_event("SLEEPING,1,EXEC_WAIT")
            time.sleep(1)
            order_info = self.order_status(order_id)

        if order_info['status'] not in CLOSED_STATES:
            record_event("SLEEPING,1,EXEC_WAIT")
            time.sleep(1)
            order_info = self.order_status(order_id)

        if order_info['status'] not in CLOSED_STATES:
            record_event("SLEEPING,5,EXEC_WAIT")
            time.sleep(5)
            order_info = self.order_status(order_id)

        print 'second print'
        print order_info

        assert(order_info['status'] in CLOSED_STATES)

        filled_qty = Decimal(0)
        total_price = Decimal(0)
        average_price = Decimal(0)

        for tx in order_info['transactions']:
            filled_qty += Decimal(tx[symbol_to_bitstamp(pair.token)])
            total_price += Decimal(tx[symbol_to_bitstamp(pair.currency)])

        if filled_qty > Decimal(0):
            average_price = total_price / filled_qty

        record_event("EXEC,%s,%s,%s,%s,%s,%0.9f,%0.9f" % (side.upper(), reason, self.name, pair.token, pair.currency, filled_qty, average_price))

        return filled_qty
