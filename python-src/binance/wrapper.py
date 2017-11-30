from decimal import *
from exchange import Exchange
from logger import record_event
from binance.api import api

def pair_name_to_binance(pair):
    p = pair.split('-')
    return "%s%s" % (p[0], p[1])

PAIRS = {
    'ADA-BTC': {
        'price_decimals': 8,
        'lot_decimals': 0
    },
    'ADA-ETH': {
        'price_decimals': 8,
        'lot_decimals': 0
    },
    'BAT-BTC': {
        'price_decimals': 8,
        'lot_decimals': 0
    },
    'BAT-ETH': {
        'price_decimals': 8,
        'lot_decimals': 0
    },
    'POWR-BTC': {
        'price_decimals': 8,
        'lot_decimals': 0
    },
    'POWR-ETH': {
        'price_decimals': 8,
        'lot_decimals': 0
    },
    'ZEC-BTC': {
        'price_decimals': 6,
        'lot_decimals': 3
    },
    'ZEC-ETH': {
        'price_decimals': 5,
        'lot_decimals': 3
    },
    'BCC-BTC': {
        'price_decimals': 6,
        'lot_decimals': 3
    },
    'BCC-ETH': {
        'price_decimals': 5,
        'lot_decimals': 3
    },
    'BCC-USDT': {
        'price_decimals': 2,
        'lot_decimals': 5
    },
    'ARK-BTC': {
        'price_decimals': 7,
        'lot_decimals': 2
    },
    'ARK-ETH': {
        'price_decimals': 6,
        'lot_decimals': 2
    },
    'XMR-BTC': {
        'price_decimals': 6,
        'lot_decimals': 3
    },
    'XMR-ETH': {
        'price_decimals': 5,
        'lot_decimals': 3
    },
    'RCN-BTC': {
        'price_decimals': 8,
        'lot_decimals': 0
    },
    'RCN-ETH': {
        'price_decimals': 8,
        'lot_decimals': 0
    },
    'KMD-BTC': {
        'price_decimals': 7,
        'lot_decimals': 2
    },
    'KMD-ETH': {
        'price_decimals': 6,
        'lot_decimals': 2
    },
    'STORJ-BTC': {
        'price_decimals': 8,
        'lot_decimals': 0
    },
    'STORJ-ETH': {
        'price_decimals': 7,
        'lot_decimals': 0
    },
    'ENG-BTC': {
        'price_decimals': 8,
        'lot_decimals': 0
    },
    'ENG-ETH': {
        'price_decimals': 7,
        'lot_decimals': 0
    },
    'AST-BTC': {
        'price_decimals': 8,
        'lot_decimals': 0
    },
    'AST-ETH': {
        'price_decimals': 7,
        'lot_decimals': 0
    },
    'MTL-BTC': {
        'price_decimals': 6,
        'lot_decimals': 2
    },
    'MTL-ETH': {
        'price_decimals': 6,
        'lot_decimals': 2
    },
    'DASH-BTC': {
        'price_decimals': 6,
        'lot_decimals': 3
    },
    'DASH-ETH': {
        'price_decimals': 5,
        'lot_decimals': 3
    },
    'SALT-BTC': {
        'price_decimals': 6,
        'lot_decimals': 2
    },
    'SALT-ETH': {
        'price_decimals': 6,
        'lot_decimals': 2
    },
    'SNM-BTC': {
        'price_decimals': 8,
        'lot_decimals': 0
    },
    'SNM-ETH': {
        'price_decimals': 8,
        'lot_decimals': 0
    },
    'FUN-BTC': {
        'price_decimals': 8,
        'lot_decimals': 0
    },
    'FUN-ETH': {
        'price_decimals': 8,
        'lot_decimals': 0
    },
    'KNC-BTC': {
        'price_decimals': 8,
        'lot_decimals': 0
    },
    'KNC-ETH': {
        'price_decimals': 8,
        'lot_decimals': 0
    },
    'SNGLS-BTC': {
        'price_decimals': 8,
        'lot_decimals': 0
    },
    'SNGLS-ETH': {
        'price_decimals': 8,
        'lot_decimals': 0
    },
    'STRAT-BTC': {
        'price_decimals': 6,
        'lot_decimals': 2
    },
    'STRAT-ETH': {
        'price_decimals': 6,
        'lot_decimals': 2
    },
    'ZRX-ETH': {
        'price_decimals': 8,
        'lot_decimals': 0
    },
    'ZRX-BTC': {
        'price_decimals': 8,
        'lot_decimals': 0
    },
    'OMG-ETH': {
        'price_decimals': 6,
        'lot_decimals': 2
    },
    'OMG-BTC': {
        'price_decimals': 6,
        'lot_decimals': 2
    },
    'OAX-ETH': {
        'price_decimals': 7,
        'lot_decimals': 0
    },
    'SNT-ETH': {
        'price_decimals': 8,
        'lot_decimals': 0
    },
    'DNT-ETH': {
        'price_decimals': 8,
        'lot_decimals': 0
    },
    'MCO-ETH': {
        'price_decimals': 6,
        'lot_decimals': 2
    },
    'QTUM-ETH': {
        'price_decimals': 6,
        'lot_decimals': 2
    },
    'ICN-BTC': {
        'price_decimals': 8,
        'lot_decimals': 0
    },
    'ICN-ETH': {
        'price_decimals': 7,
        'lot_decimals': 0
    },
    'ETH-BTC': {
        'price_decimals': 6,
        'lot_decimals': 3
    },
    'LTC-BTC': {
        'price_decimals': 6,
        'lot_decimals': 2
    },
    'MCO-BTC': {
        'price_decimals': 6,
        'lot_decimals': 2
    },
    'QTUM-BTC': {
        'price_decimals': 6,
        'lot_decimals': 2
    },
    'BNT-BTC': {
        'price_decimals': 8,
        'lot_decimals': 0
    },
    'BTC-USDT': {
        'price_decimals': 2,
        'lot_decimals': 6
    },
    'ETH-USDT': {
        'price_decimals': 2,
        'lot_decimals': 5
    }
}

class Binance(Exchange):
    def __init__(self):
        Exchange.__init__(self, 'BINANCE')

        with open('binance.keys', 'r') as api_key:
            self.api = api(api_key.readline().strip(), api_key.readline().strip())

        self.symbols = ['BTC','ETH','USDT','LTC','BNT','OAX','SNT','DNT','MCO','QTUM','ICN','OMG','ZRX','STRAT','SNGLS','KNC','SNM','FUN','SALT','DASH','ENG','AST','MTL','STORJ','RCN','KMD','ARK','XMR','BCC','POWR','ZEC','BAT','ADA']
        self.fees = {}

        account_info = self.api.account_info()

        for ticker in PAIRS:
            self.fees[ticker] = Decimal('0.001')

    def pair_name(self, pair):
        return "%s%s" % (pair.token.upper(), pair.currency.upper())

    def deposit_address(self, symbol):
        return {
            "ETH":"0xfd0b4f1e367ce7e0ee598652f27a58a10f0aa522",
            "OAX":"0xfd0b4f1e367ce7e0ee598652f27a58a10f0aa522",
            "SNT":"0xfd0b4f1e367ce7e0ee598652f27a58a10f0aa522",
            "DNT":"0xfd0b4f1e367ce7e0ee598652f27a58a10f0aa522",
            "MCO":"0xfd0b4f1e367ce7e0ee598652f27a58a10f0aa522",
            "QTUM":"Qb8TkuiYHiiMULAnwvNwxiiX7ZysRDMGuU",
            "ICN":"0xfd0b4f1e367ce7e0ee598652f27a58a10f0aa522",
            "BTC":"1B6pVbhmQ6un24QB7DCSNoEmbe91bZ41YJ",
            "USDT":"17VxEQNdw7pW1iooCzZAqHAvJ47tiR28py",
            "LTC":"LTitpZQ59FeFFaBD47osy5UkfG6FUMiTux",
            "BNT":"0xfd0b4f1e367ce7e0ee598652f27a58a10f0aa522",
            "ZRX":"0xfd0b4f1e367ce7e0ee598652f27a58a10f0aa522",
            "OMG":"0xfd0b4f1e367ce7e0ee598652f27a58a10f0aa522",
            "STRAT":"Sa5vFpjh4MitFCPxpkKXbp16rYe4n9n72A",
            "SNGLS":"0xfd0b4f1e367ce7e0ee598652f27a58a10f0aa522",
            "KNC":"0xfd0b4f1e367ce7e0ee598652f27a58a10f0aa522",
            "SNM":"0xfd0b4f1e367ce7e0ee598652f27a58a10f0aa522",
            "SALT":"0xfd0b4f1e367ce7e0ee598652f27a58a10f0aa522",
            "ENG":"0xfd0b4f1e367ce7e0ee598652f27a58a10f0aa522",
            "AST":"0xfd0b4f1e367ce7e0ee598652f27a58a10f0aa522",
            "MTL":"0xfd0b4f1e367ce7e0ee598652f27a58a10f0aa522",
            "RCN":"0xfd0b4f1e367ce7e0ee598652f27a58a10f0aa522",
            "KMD":"R9n3zB5Xybkb9aj83LouA8qX6KwWUAXYea",
            "STORJ":"0xfd0b4f1e367ce7e0ee598652f27a58a10f0aa522",
            "DASH":"Xavveg4yp4JTni7y9hZt512ZX4zLf8BifB",
            "ARK":"AbRdSsp8mgEgLciC8r3xLJQUdwhMKwirjF",
            "XMR":"44tLjmXrQNrWJ5NBsEj2R77ZBEgDa3fEe9GLpSf2FRmhexPvfYDUAB7EXX1Hdb3aMQ9FLqdJ56yaAhiXoRsceGJCRS3Jxkn",
            "BCC":"1B6pVbhmQ6un24QB7DCSNoEmbe91bZ41YJ",
            "POWR":"0xfd0b4f1e367ce7e0ee598652f27a58a10f0aa522",
            "ZEC":"t1afnaVLGdDMpDeAZD4LrW9u56R4YAhJXR4",
            "BAT":"0xfd0b4f1e367ce7e0ee598652f27a58a10f0aa522",
            "ADA":"DdzFFzCqrhszh9atnDUPySMZyBJqeyc4w6hZY67RH7uyXHF9QKSGZkey8VRBnmi2nRWUxS8J3CVu32wmkMYXdiRkoVU3evuZQCUv5hw8",
            "FUN":"0xfd0b4f1e367ce7e0ee598652f27a58a10f0aa522"
        }[symbol]

    def deposit_message(self, symbol):
        msg_map = {
            "XMR":"0264ae179190b497fc85a4ccfda4e21d88a3f1f4934112509735276e066124c2"
        }
        return msg_map[symbol]

    def withdraw(self, dest, symbol, amount):
        address = dest.deposit_address(symbol)
        message = ""
        key_name = dest.name.lower() + "_" + symbol.lower()

        if symbol in ['SNGLS']: # SNGLS fractions cannot be withdrawns
            amount = amount.split('.')[0]

        event = "WITHDRAW,%s,%s,%s,%s,%s" % (self.name, dest.name, symbol, amount, address)
        if symbol in self.require_deposit_message:
            message = dest.deposit_message(symbol)

        if message: # api withdrawals with message are not supported?
            event += "," + message
            record_event(event)
        else:
            record_event(event)
            print "BINANCE WITHDRAWAL"
            print self.api.withdraw(symbol, amount, address, key_name)

    def refresh_balances(self):
        for info in self.api.account_info()['balances']:
            if info['asset'] in self.symbols:
                self.balance[info['asset']] = Decimal(info['free'])

    def any_open_orders(self):
        for info in self.api.account_info()['balances']:
            if Decimal(info['locked']) != Decimal("0"):
                return True
        return False

    def cancel_all_orders(self):
        if self.any_open_orders():
            for pair in self.fees:
                for order in self.api.open_orders(pair_name_to_binance(pair)):
                    print "CANCELLING BINANCE ORDER"
                    print order
                    self.api.cancel_order(order)

    def trade_ioc(self, pair, side, price, amount, reason):
        price = ("%0." + str(PAIRS[str(pair)]['price_decimals']) + "f") % price
        amount = ("%0." + str(PAIRS[str(pair)]['lot_decimals']) + "f") % amount

        print "submitting binance trade: %s %s %s" % (str(pair), price, amount)

        order = self.api.new_order(side.upper(), self.pair_name(pair), price, amount)
        print order
        order_info = self.api.order_info(order)
        print order_info

        ctr = 0
        while order_info['status'] not in ['FILLED','CANCELED','REJECTED','EXPIRED']:
            time.sleep(1)
            order_info = self.api.order_info(order)
            print order_info
            ctr += 1
            if ctr > 5:
                print "BINANCE IOC ORDER NEVER CLOSED"
                raise Exception()

        filled_qty = Decimal(order_info['executedQty'])

        record_event("EXEC,%s,%s,%s,%s,%s,%0.9f,%s" % (side.upper(), reason, self.name, pair.token, pair.currency, filled_qty, price))

        return filled_qty
