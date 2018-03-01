from decimal import *
from exchange import Exchange
from order import Order
from logger import record_event
import json
import time

from kucoin.client import Client

PAIRS = {
    'AION-BTC': {
        'price_decimals' : 8,
        'lot_decimals' : 6
    },
    'AION-ETH': {
        'price_decimals' : 6,
        'lot_decimals' : 6
    },
    'BCC-BTC': {
        'price_decimals' : 8,
        'lot_decimals' : 8
    },
    'BCC-ETH': {
        'price_decimals' : 6,
        'lot_decimals' : 8
    },
    'BCC-USDT': {
        'price_decimals' : 6,
        'lot_decimals' : 8
    },
    'BTC-USDT': {
        'price_decimals' : 6,
        'lot_decimals' : 8
    },
    'CVC-BTC': {
        'price_decimals' : 8,
        'lot_decimals' : 4
    },
    'CVC-ETH': {
        'price_decimals' : 6,
        'lot_decimals' : 4
    },
    'DASH-BTC': {
        'price_decimals' : 8,
        'lot_decimals' : 8
    },
    'DASH-ETH': {
        'price_decimals' : 6,
        'lot_decimals' : 8
    },
    'ETH-BTC': {
        'price_decimals' : 8,
        'lot_decimals' : 6
    },
    'ETH-USDT': {
        'price_decimals' : 6,
        'lot_decimals' : 6
    },
    'KNC-BTC': {
        'price_decimals' : 8,
        'lot_decimals' : 4
    },
    'KNC-ETH': {
        'price_decimals' : 6,
        'lot_decimals' : 4
    },
    'LTC-BTC': {
        'price_decimals' : 8,
        'lot_decimals' : 6
    },
    'LTC-ETH': {
        'price_decimals' : 6,
        'lot_decimals' : 6
    },
    'LTC-USDT': {
        'price_decimals' : 6,
        'lot_decimals' : 6
    },
    'NEO-BTC': {
        'price_decimals' : 8,
        'lot_decimals' : 6
    },
    'NEO-ETH': {
        'price_decimals' : 6,
        'lot_decimals' : 6
    },
    'NEO-USDT': {
        'price_decimals' : 6,
        'lot_decimals' : 6
    },
    'OMG-BTC': {
        'price_decimals' : 8,
        'lot_decimals' : 4
    },
    'OMG-ETH': {
        'price_decimals' : 6,
        'lot_decimals' : 4
    },
    'POWR-BTC': {
        'price_decimals' : 8,
        'lot_decimals' : 6
    },
    'POWR-ETH': {
        'price_decimals' : 6,
        'lot_decimals' : 6
    },
    'QTUM-BTC': {
        'price_decimals' : 8,
        'lot_decimals' : 4
    },
    'REQ-BTC': {
        'price_decimals' : 8,
        'lot_decimals' : 4
    },
    'REQ-ETH': {
        'price_decimals' : 6,
        'lot_decimals' : 4
    },
    'SNT-BTC': {
        'price_decimals' : 8,
        'lot_decimals' : 4
    },
    'SNT-ETH': {
        'price_decimals' : 6,
        'lot_decimals' : 4
    },
    'VEN-BTC': {
        'price_decimals' : 8,
        'lot_decimals' : 4
    },
    'VEN-ETH': {
        'price_decimals' : 6,
        'lot_decimals' : 4
    },
    'XRB-BTC': {
        'price_decimals' : 8,
        'lot_decimals' : 6
    },
    'XRB-ETH': {
        'price_decimals' : 6,
        'lot_decimals' : 6
    },
    'XRB-USDT': {
        'price_decimals' : 6,
        'lot_decimals' : 6
    }
}

def symbol_from_kucoin(symbol):
    if symbol == "BCH":
        return "BCC"
    else:
        return symbol

def symbol_to_kucoin(symbol):
    if symbol == "BCC":
        return "BCH"
    else:
        return symbol

class KuCoin(Exchange):
    def __init__(self):
        Exchange.__init__(self, 'KUCOIN')
        with open('kucoin.keys') as secrets_file:
            secrets = json.load(secrets_file)
            self.api = Client(secrets['key'], secrets['secret'])

        # self.symbols = ['BTC','ETH','USDT','AION','BCC','CVC','DASH','KNC','LTC','NEO','OMG','POWR','QTUM','REQ','SNT','VEN','XRB','POLY','DRGN']
        self.symbols = ['BTC','ETH','USDT','AION','CVC','KNC','NEO','OMG','POWR','QTUM','REQ','VEN','XRB','POLY','DRGN']

        for pair in PAIRS.keys():
            self.fees[pair] = Decimal('0.001')

    def pair_name(self, pair):
        return "%s-%s" % (symbol_to_kucoin(pair.token), symbol_to_kucoin(pair.currency))

    def deposit_address(self, symbol):
        addr_map = {
            'BTC':'1PHuS8vBkRoEVMdvNLjht759wTkeh3d2NS',
            'ETH':'0x1f1284066af0d1357d1d9f1abc97176255145fd4',
            'USDT':'1LJA9JmLiVCeLaqybUsGYegVB1Pw5w5qck',
            'AION':'0x1f1284066af0d1357d1d9f1abc97176255145fd4',
            'BCC':'14X8ZvjWNDcXhYthVUC2u97Z3y2ZyYQo5u',
            'CVC':'0x1f1284066af0d1357d1d9f1abc97176255145fd4',
            'DASH':'XwPtoN2tF6r37xhMq6NkxBRen8KiLb7TsC',
            'KNC':'0x1f1284066af0d1357d1d9f1abc97176255145fd4',
            'LTC':'LaMeF588zsBX2KdUyeprPeH7sQjSvCQFY5',
            'NEO':'ANWN7HsPAWG1pxEwfP8D6LpSEDAH5pFC1W',
            'OMG':'0x1f1284066af0d1357d1d9f1abc97176255145fd4',
            'POWR':'0x1f1284066af0d1357d1d9f1abc97176255145fd4',
            'QTUM':'QYLAj3dKCuXPaR9Ajz2it8Wb25qG1bGkWn',
            'REQ':'0x1f1284066af0d1357d1d9f1abc97176255145fd4',
            'SNT':'0x1f1284066af0d1357d1d9f1abc97176255145fd4',
            'VEN':'0x1f1284066af0d1357d1d9f1abc97176255145fd4',
            'XRB':'0x1f1284066af0d1357d1d9f1abc97176255145fd4',
            'POLY':'0x1f1284066af0d1357d1d9f1abc97176255145fd4',
            'DRGN':'0x1f1284066af0d1357d1d9f1abc97176255145fd4'
        }

        assert(self.api.get_deposit_address(symbol_to_kucoin(symbol))['address'] == addr_map[symbol])

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

    def refresh_balances(self, symbols=None):
        if symbols:
            for symbol in symbols:
                self.balance[symbol] = Decimal(self.api.get_coin_balance(symbol_to_kucoin(symbol))['balanceStr'])
        else:
            pages = [self.api.get_all_balances(limit=20)]
            while len(pages) < pages[0]['pageNos']:
                pages = pages + [self.api.get_all_balances(limit=20, page=len(pages)+1)]

            for page in pages:
                for info in page['datas']:
                    if symbol_from_kucoin(info['coinType']) in self.symbols:
                        self.balance[symbol_from_kucoin(info['coinType'])] = Decimal(info['balanceStr'])

    def any_open_orders(self):
        return False # That's a bold strategy Cotton, Let's see if it pays off
        # Consider doing something with the frozen balance

    def cancel_all_orders(self):
        self.api.cancel_all_orders()

    def trade_ioc(self, pair, side, price, amount, reason):
        price = ("%0." + str(PAIRS[str(pair)]['price_decimals']) + "f") % price
        amount = ("%0." + str(PAIRS[str(pair)]['lot_decimals']) + "f") % amount

        order_info = self.api.create_order(self.pair_name(pair), side.upper(), price, amount)

        print 'first print'
        print order_info
        order_id = order_info['orderOid']

        order_info = self.api.get_order_details(self.pair_name(pair), side.upper(), order_id=order_id)

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
