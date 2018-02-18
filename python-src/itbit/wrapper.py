from decimal import *
from exchange import Exchange
from order import Order
from logger import record_event
import json
import time

from itbit.api import itBitApiConnection

PAIRS = {
    'BTC-USD': {
        'price_decimals' : 2,
        'lot_decimals' : 4
    }
}
def symbol_from_itbit(symbol):
    if symbol == 'XBT':
        return 'BTC'
    else:
        return symbol

def symbol_to_itbit(symbol):
    if symbol == 'BTC':
        return 'XBT'
    else:
        return symbol

def order_is_open(order_info):
    return order_info['status'] in ['submitted', 'open']

class ItBit(Exchange):
    def __init__(self):
        Exchange.__init__(self, 'ITBIT')
        with open('itbit.keys') as secrets_file:
            secrets = json.load(secrets_file)
            self.api = itBitApiConnection(secrets['key'], secrets['secret'], secrets['userId'])

        self.symbols = ['USD','BTC']
        self.fees['BTC-USD'] = Decimal('0.002')

        wallets = self.api.get_all_wallets().json()
        assert(len(wallets) == 1)
        self.wallet_id = self.api.get_all_wallets().json()[0]['id']

    def pair_name(self, pair):
        return "%s%s" % (symbol_to_itbit(pair.token), symbol_to_itbit(pair.currency))

    def deposit_address(self, symbol):
        addr_map = {
            'BTC':'3Jqpg73du2dy1R9gXFN3PDSzdqjA8z76By',
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
        for info in self.api.get_all_wallets().json()[0]['balances']:
            if symbol_from_itbit(info['currency']) in self.symbols:
                self.balance[symbol_from_itbit(info['currency'])] = Decimal(info['availableBalance'])

    def get_open_orders(self):
        return self.api.get_wallet_orders(self.wallet_id, {'status':'open'}).json()

    def get_submitted_orders(self):
        return self.api.get_wallet_orders(self.wallet_id, {'status':'submitted'}).json()

    def any_open_orders(self):
        if len(self.get_open_orders()) > 0:
            return True
        if len(self.get_submitted_orders()) > 0:
            return True

        return False

    def cancel_all_orders(self):
        for order in self.get_open_orders():
            self.api.cancel_order(self.wallet_id, order['id'])
        for order in self.get_submitted_orders():
            self.api.cancel_order(self.wallet_id, order['id'])

    def trade_ioc(self, pair, side, price, amount, reason):
        price = ("%0." + str(PAIRS[str(pair)]['price_decimals']) + "f") % price
        amount = ("%0." + str(PAIRS[str(pair)]['lot_decimals']) + "f") % amount

        order_info = self.api.create_order(self.wallet_id, side, symbol_to_itbit(pair.token), amount, price, self.pair_name(pair)).json()

        print 'first print'
        print order_info
        order_id = order_info['id']

        if order_is_open(order_info): # try to get order result immediately
            order_info = self.api.get_order(self.wallet_id, order_id).json()

        if order_is_open(order_info): # still not complete, cancel, wait, and retry
            record_event("SLEEPING,1,EXEC_WAIT")
            time.sleep(1)
            self.api.cancel_order(self.wallet_id, order_id)

            record_event("SLEEPING,1,EXEC_WAIT")
            time.sleep(1)
            order_info = self.api.get_order(self.wallet_id, order_id).json()

        print 'second print'
        print order_info

        assert(not order_is_open(order_info))
        filled_qty = Decimal(order_info['amountFilled'])
        average_price = Decimal(order_info['volumeWeightedAveragePrice'])

        record_event("EXEC,%s,%s,%s,%s,%s,%0.9f,%0.9f" % (side.upper(), reason, self.name, pair.token, pair.currency, filled_qty, average_price))

        return filled_qty
