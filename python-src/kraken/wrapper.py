from decimal import *
from time import sleep
from kraken.api import API
from kraken.connection import Connection
from exchange import Exchange
from order import Order
from logger import record_event
import json
import pprint
import sys
import time

def symbol_from_kraken(symbol):
    if symbol == "XXBT":
        return "BTC"
    elif symbol == "GNO" or symbol == "DASH":
        return symbol
    elif symbol == "BCH":
        return "BCC"
    else:
        return symbol[1:]

def symbol_to_kraken(symbol):
    if symbol == "BTC":
        return "XXBT"
    elif symbol == "GNO" or symbol == "DASH":
        return symbol
    elif symbol == "BCC":
        return "BCH"
    else:
        return "X%s" % symbol

def asset_name(symbol):
    if symbol == "BCC":
        return "BCH"
    elif symbol == "BTC":
        return "XBT"
    else:
        return symbol

class Kraken(Exchange):
    def __init__(self):
        Exchange.__init__(self, "KRAKEN")
        self.conn = Connection()
        self.api = API()
        self.price_decimals = dict()
        self.lot_decimals = dict()
        self.api.load_key('kraken.keys')

        self.pair_name_map = {}

        with open('kraken_info.json') as f:
            self.tickers = json.loads(f.read())['result'].items()

        self.symbols = ['BTC', 'ETH', 'LTC', 'ICN', 'MLN', 'REP', 'DASH', 'BCC', 'XMR', 'ZEC', 'XRP', 'XLM']
        for pair,info in self.tickers:
            if '.' in pair: # some duplicate entries have a period, unsure why
                continue

            token = symbol_from_kraken(info['base'])
            currency = symbol_from_kraken(info['quote'])
            if token in self.symbols and currency in self.symbols:

                uniform_ticker = "%s-%s" % (token, currency)
                self.pair_name_map[uniform_ticker] = pair

                # [vol,fee] = info['fees'][4]
                # assert(vol == 500000)
                self.fees[uniform_ticker] = 0 # trading temporarily free at kraken #Decimal(fee) / 100
                self.price_decimals[uniform_ticker] = info['pair_decimals']
                self.lot_decimals[uniform_ticker] = min(info['lot_decimals'], info['pair_decimals'])

    def query_private(self, method, args):
        return self.api.query_private(method, args, self.conn)

    def query_public(self, method, args):
        return self.api.query_public(method, args, self.conn)

    def pair_name(self, pair):
        return self.pair_name_map[str(pair)]

    def deposit_address(self, symbol):
        addr_map = {
            "BTC":"3DraSxHFsbMd2vPFXfF9Q62ruzpt2wcKdt",
            "MLN":"0xe43598b00615def726d2668458fc6a21865691c3",
            "ETH":"0x7ed125961654434849c074a3edcd55900e29d916",
            "ICN":"0xc404050987865b643855eb14313f2abf5a63f046",
            "LTC":"LZKevLmwWEZTJcZigaNwAmoavH9zi1fRGW",
            "REP":"0x24161fdfe1d96043f3f7459b444cbbc8c188c8cc",
            "DASH":"XuQdnZqUvkgqgoyP9oizv3tS1nxpLuugyk",
            "BCC":"1BhN1Mpwa6j7JsEWyWuckYAmnR8iukijmx",
            "XMR":"4GdoN7NCTi8a5gZug7PrwZNKjvHFmKeV11L6pNJPgj5QNEHsN6eeX3DaAQFwZ1ufD4LYCZKArktt113W7QjWvQ7CWG18YB7CuKmUY4QxAH",
            "ZEC":"t1a4ErZkCfqfckwojUh6iRheDSHHVQcNQdk",
            "XRP":"rLHzPsX6oXkzU2qL12kHCH8G8cnZv1rBJh",
            "XLM":"GA5XIGA5C7QTPTWXQHY6MCJRMTRZDOSHR6EFIBNDQTCQHG262N4GGKTM"
        }
        method_map = {
            "BTC":"Bitcoin",
            "LTC":"Litecoin",
            "ETH":"Ether (Hex)",
            "REP":"REP",
            "ICN":"ICN",
            "MLN":"MLN",
            "DASH":"Dash",
            "BCC":"Bitcoin Cash",
            "XMR":"Monero",
            "ZEC":"Zcash (Transparent)",
            "XRP":"Ripple XRP",
            "XLM":"Stellar XLM"
        }

        addr_info = filter(lambda info: info['address'] == addr_map[symbol], self.query_private('DepositAddresses', {'asset':asset_name(symbol), 'method':method_map[symbol]})['result'])[0]
        assert(int(addr_info['expiretm']) == 0)
        assert(addr_info['address'] == addr_map[symbol])

        return addr_info['address']

    def deposit_message(self, symbol):
        msg_map = {
            "XMR":"",
            "XRP":"3732985062",
            "XLM":"1843521132"
        }
        return msg_map[symbol]

    def withdraw(self, dest, symbol, amount):
        event = "WITHDRAW,%s,%s,%s,%s,%s" % (self.name, dest.name, symbol, amount, dest.deposit_address(symbol))
        if symbol in self.require_deposit_message:
            event += "," + dest.deposit_message(symbol)
        record_event(event)

        key_name = dest.name.lower() + "_" + symbol.lower()
        print "KRAKEN WITHDRAWAL"
        print self.query_private('Withdraw', {'asset':asset_name(symbol), 'key':key_name, 'amount':amount})

    def refresh_balances(self):
        balances = self.query_private('Balance', {})['result']

        for symbol in self.symbols:
            if symbol_to_kraken(symbol) in balances:
                self.balance[symbol] = Decimal(balances[symbol_to_kraken(symbol)])
            else:
                self.balance[symbol] = Decimal(0)

    def order_info(self, txid):
        return self.query_private('QueryOrders', {'txid':txid})['result'][txid]

    def trade_ioc(self, pair, side, price, amount, reason):
        ret = dict()
        try:
            ret = self.query_private('AddOrder', {
                'pair' : self.pair_name(pair),
                'type' : side,
                'ordertype' : 'limit',
                'price' : ("%0." + str(self.price_decimals[str(pair)]) + "f") % price,
                'volume' : ("%0." + str(self.lot_decimals[str(pair)]) + "f") % amount,
                'expiretm' : '+10'
            })
            txid = ret['result']['txid'][0]
        except:
            pprint.PrettyPrinter(indent=4).pprint(ret)
            sys.exit(1)

        self.query_private('CancelOrder', {'txid':txid})
        order_info = self.order_info(txid)
        while order_info['status'] == 'pending' or order_info['status'] == 'open':
            record_event("IOC_FAIL,KRAKEN")
            sleep(1)
            self.query_private('CancelOrder', {'txid':txid})
            order_info = self.order_info(txid)

        filled_qty = Decimal(order_info['vol_exec'])

        record_event("EXEC,%s,%s,%s,%s,%s,%0.8f,%0.8f" % (side.upper(), reason, self.name, pair.token, pair.currency, filled_qty, price))

        return filled_qty

    def cancel(self, txid):
        return self.query_private('CancelOrder', {'txid':txid})

    def any_open_orders(self):
        for txid,info in self.active_orders().items():
            return True

        return False

    def cancel_all_orders(self):
        for txid,info in self.active_orders().items():
            record_event("CANCELALL,%s,%s" % (self.name,txid))
            self.cancel(txid)

    def active_orders(self):
        return self.query_private('OpenOrders', {})['result']['open']
