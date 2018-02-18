from decimal import *
from exchange import Exchange
from order import Order
from logger import record_event
import json
import time

import gdax

def symbol_from_gdax(symbol):
    if symbol == 'BCH':
        return 'BCC'
    else:
        return symbol

def symbol_to_gdax(symbol):
    if symbol == 'BCC':
        return 'BCH'
    else:
        return symbol

PAIRS = dict()
INFO_CACHE_PATH = 'gdax_info.json'
def convert_tick_size_to_decimal_position(s):
    n = Decimal(s)
    ret = 0
    if n > Decimal('1'):
        raise Exception()

    while n < Decimal('1'):
        n = n * Decimal('10')
        ret = ret + 1

    return ret

with open(INFO_CACHE_PATH) as f:
    info = json.loads(f.read())
    for pair_info in info:
        PAIRS["%s-%s" % (symbol_from_gdax(pair_info['base_currency']), symbol_from_gdax(pair_info['quote_currency']))] = {
            'price_decimals' : convert_tick_size_to_decimal_position(pair_info['quote_increment']),
            'lot_decimals' : 8,
            'lot_minimum' : pair_info['base_min_size'],
            'gdax_id' : pair_info['id']
        }

class GDAX(Exchange):
    def __init__(self):
        Exchange.__init__(self, 'GDAX')
        with open('gdax.keys') as secrets_file:
            secrets = json.load(secrets_file)
            self.api = gdax.AuthenticatedClient(secrets['key'], secrets['secret'], secrets['passphrase'])

        self.symbols = ['USD','BTC','ETH','LTC','BCC']

        for ticker in PAIRS:
            if ticker.startswith('LTC') or ticker.startswith('ETH'):
                self.fees[ticker] = Decimal('0.003')
            else:
                self.fees[ticker] = Decimal('0.0025')

    def pair_name(self, pair):
        return "%s-%s" % (symbol_to_gdax(pair.token), symbol_to_gdax(pair.currency))

    def deposit_address(self, symbol):
        addr_map = {
            'BTC':'13dqE8EaauY8uzQCdgiadX16eggWKwG9rJ',
            'LTC':'LcjF3N5KU3QVisZtD1FzdCFdj1x3vGz3Yv',
            'ETH':'0xE2332C48a43cD0f9E802fF347F148F5924f0E1Cc',
            'BCC':'1FwKuosXyAqQy845bDsDoAsWhWsSPg3WmL',
            'USD':'SILVERGATE'
        }

        return addr_map[symbol]

    def deposit_message(self, symbol):
        return ''

    def withdraw(self, dest, symbol, amount):
        address = dest.deposit_address(symbol)
        message = ''
        event = "WITHDRAW,%s,%s,%s,%s,%s" % (self.name, dest.name, symbol, amount, address)
        if symbol in self.require_deposit_message:
            event += ',' + dest.deposit_message(symbol)

        record_event(event)

    def refresh_balances(self):
        for info in self.api.get_accounts():
            if symbol_from_gdax(info['currency']) in self.symbols:
                self.balance[symbol_from_gdax(info['currency'])] = Decimal(info['balance'])

    def any_open_orders(self):
        return len(self.api.get_orders()[0]) > 0

    def cancel_all_orders(self):
        if self.any_open_orders():
            for pair,pair_info in PAIRS.iteritems():
                self.api.cancel_all(product=pair_info['gdax_id'])

    def trade_ioc(self, pair, side, price, amount, reason):
        price = ("%0." + str(PAIRS[str(pair)]['price_decimals']) + "f") % price
        amount = ("%0." + str(PAIRS[str(pair)]['lot_decimals']) + "f") % amount

        if side == 'buy':
            order_info = self.api.buy(product_id=self.pair_name(pair),
                                  size=amount, price=price, type='limit', time_in_force='IOC')
        else:
            order_info = self.api.sell(product_id=self.pair_name(pair),
                                  size=amount, price=price, type='limit', time_in_force='IOC')

        print 'first print'
        print order_info
        order_id = order_info['id']

        if order_info['status'] != 'done': # try to get order result immediately
            order_info = self.api.get_order(order_id)

        if 'id' in order_info and order_info['status'] != 'done': # still not complete, cancel, wait, and retry
            record_event("SLEEPING,1,EXEC_WAIT")
            time.sleep(1)
            self.api.cancel_order(order_id)

            record_event("SLEEPING,1,EXEC_WAIT")
            time.sleep(1)
            order_info = self.api.get_order(order_id)

        print 'second print'
        print order_info

        if 'id' not in order_info: # unable to find order means 0 fill
            filled_qty = Decimal(0)
            average_price = Decimal(0)
        else:
            assert(order_info['status'] == 'done')
            filled_qty = Decimal(order_info['filled_size'])
            average_price = Decimal(order_info['executed_value']) / Decimal(order_info['filled_size'])

        record_event("EXEC,%s,%s,%s,%s,%s,%0.9f,%0.9f" % (side.upper(), reason, self.name, pair.token, pair.currency, filled_qty, average_price))

        return filled_qty
