from decimal import *
from exchange import Exchange
from order import Order
from logger import record_event
from fees import FEES
import json
import time

from bitflyer.api import API

PAIRS = {
    'BTC-USD': {
        'price_decimals' : 2,
        'lot_decimals' : 5
    }
}

def symbol_from_bitflyer(symbol):
    return symbol

def symbol_to_bitflyer(symbol):
    return symbol

def convert_pair_name(pair):
    l = pair.split('-')
    return "%s_%s" % (symbol_to_bitflyer(l[0]), symbol_to_bitflyer(l[1]))

class BitFlyer(Exchange):
    def __init__(self):
        Exchange.__init__(self, 'BITFLYER')
        with open('bitflyer.keys') as secrets_file:
            secrets = json.load(secrets_file)
            self.api = API(str(secrets['key']), str(secrets['secret']), timeout=5)

        self.symbols = ['USD','BTC']
        self.fees['BTC-USD'] = FEES[self.name].taker

    def pair_name(self, pair):
        return "%s_%s" % (symbol_to_bitflyer(pair.token), symbol_to_bitflyer(pair.currency))

    def deposit_address(self, symbol):
        addr_map = {
            'BTC':'36VsjQkwn7cPFAEp5iDV9wPKLN8Nzacthb',
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
        for info in self.api.getbalance():
            if symbol_from_bitflyer(info['currency_code']) in self.symbols:
                self.balance[symbol_from_bitflyer(info['currency_code'])] = Decimal(info['available'])

    def any_open_orders(self):
        assert(len(PAIRS) == 1)
        return len(self.api.getchildorders(product_code='BTC_USD', child_order_state='ACTIVE')) > 0

    def cancel_all_orders(self):
        assert(len(PAIRS) == 1)
        self.api.cancelallchildorders(product_code='BTC_USD')

    def trade_ioc(self, pair, side, price, amount, reason):
        price = ("%0." + str(PAIRS[str(pair)]['price_decimals']) + "f") % price
        amount = ("%0." + str(PAIRS[str(pair)]['lot_decimals']) + "f") % amount
        product_code = self.pair_name(pair)

        order_id = self.api.sendchildorder(product_code=product_code, side=side.upper(), size=amount, price=price,
                                           child_order_type='LIMIT', time_in_force='IOC')['child_order_acceptance_id']

        print 'first print -- order acceptance id'
        print order_id

        time.sleep(2) # wait for bitflyer matching engine to do it's thing
        order_info = self.api.getchildorders(product_code=product_code, child_order_acceptance_id=order_id)

        if len(order_info) == 0: # no orders returned could indicate no fill, sleep to confirm
            time.sleep(2) # wait a bit more for matching engine
            order_info = self.api.getchildorders(product_code=product_code, child_order_acceptance_id=order_id)

        if len(order_info) == 0: # assume this means absolutely no fills
            filled_qty = Decimal(0)
            average_price = Decimal(0)
        else:
            order_info = order_info[0]
            print 'second print -- order info print'
            print order_info

            assert(order_info['child_order_state'] != 'ACTIVE') # IOC order should never be considered active

            filled_qty = Decimal(order_info['executed_size'])
            average_price = Decimal(order_info['average_price'])

        record_event("EXEC,%s,%s,%s,%s,%s,%0.9f,%0.9f" % (side.upper(), reason, self.name, pair.token, pair.currency, filled_qty, average_price))

        return filled_qty
