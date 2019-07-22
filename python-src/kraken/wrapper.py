from decimal import *
from time import sleep
from kraken.api import API
from kraken.connection import Connection
from exchange import Exchange
from order import Order
from logger import record_event
from fees import FEES
import json
import pprint
import sys
import time

modern_symbols = ['GNO','DASH','ADA','BCH','ATOM']

def symbol_from_kraken(symbol):
    if symbol == "XXBT":
        return "BTC"
    elif symbol in modern_symbols:
        return symbol
    elif symbol == "ZUSD":
        return "USD"
    else:
        return symbol[1:]

def symbol_to_kraken(symbol):
    if symbol == "BTC":
        return "XXBT"
    elif symbol in modern_symbols:
        return symbol
    elif symbol == "USD":
        return "ZUSD"
    else:
        return "X%s" % symbol

def asset_name(symbol):
    if symbol == "BTC":
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

        self.symbols = ['USD', 'BTC', 'ETH', 'LTC', 'BCH', 'XMR', 'XRP', 'XLM', 'ADA', 'ATOM']
        for pair,info in self.tickers:
            if '.' in pair: # some duplicate entries have a period, unsure why
                continue

            token = symbol_from_kraken(info['base'])
            currency = symbol_from_kraken(info['quote'])
            if token in self.symbols and currency in self.symbols:

                uniform_ticker = "%s-%s" % (token, currency)
                self.pair_name_map[uniform_ticker] = pair

                self.fees[uniform_ticker] = FEES[self.name].taker
                self.price_decimals[uniform_ticker] = info['pair_decimals']
                self.lot_decimals[uniform_ticker] = info['lot_decimals']

    def query_private(self, method, args):
        return self.api.query_private(method, args, self.conn)

    def query_public(self, method, args):
        return self.api.query_public(method, args, self.conn)

    def pair_name(self, pair):
        return self.pair_name_map[str(pair)]

    def deposit_address(self, symbol):
        if symbol == 'USD':
            return 'SILVERGATE'

        addr_map = {
            "BTC":"38kTfMQmD53d3DED35PtahwwX84jYPUtJe",
            "MLN":"0x230b1c7981df97ac05aa5a85eb7fe8ae3a40bfd8",
            "ETH":"0xebcea4f26374764b0a564bfa36a362a4693fa5f3",
            "ICN":"0x2f6434e86066e225aa2872e4b880d6da14fc5503",
            "LTC":"LWY6VsRVhAY7LDmbV9xQJvuXNxC4HpPVeb",
            "REP":"0xed68535e57ddc72ed099a4ccb536c51ea5b07664",
            "BCH":"1C641sGmnpE9yRgfzThmKdsDdUz8QHd9H4",
            "XMR":"4GdoN7NCTi8a5gZug7PrwZNKjvHFmKeV11L6pNJPgj5QNEHsN6eeX3DaAQFwZ1ufD4LYCZKArktt113W7QjWvQ7CWDM25ByQyJ4VcAfaDe",
            "ZEC":"t1bRnuSuykATwXtNVUkYdJ5nyd9kgppEz5p",
            "XRP":"rLHzPsX6oXkzU2qL12kHCH8G8cnZv1rBJh",
            "GNO":"0x28e019139a20024559e228b70256ae369807d985",
            "ADA":"DdzFFzCqrhsy3h8kKB7no9gLEHkikCNtop1VTQkgMdeeehBU2ELLt9NPhxTMAcs99f2MnG6ABHeCXCFMc6fqd9whe1rMn9jzyc9qsqxU",
            "ATOM":"cosmos122u89vat7xsl5regrl4a43vc8pyvdrwy5mvh4l",
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
            "BCH":"Bitcoin Cash",
            "XMR":"Monero",
            "ZEC":"Zcash (Transparent)",
            "XRP":"Ripple XRP",
            "GNO":"GNO",
            "ADA":"ADA",
            "ATOM":"Cosmos",
            "XLM":"Stellar XLM"
        }

        addr_info = filter(lambda info: info['address'] == addr_map[symbol], self.query_private('DepositAddresses', {'asset':asset_name(symbol), 'method':method_map[symbol]})['result'])[0]
        assert(int(addr_info['expiretm']) == 0)
        assert(addr_info['address'] == addr_map[symbol])

        return addr_info['address']

    def deposit_message(self, symbol):
        msg_map = {
            "XMR":"",
            "ATOM":"",
            "XRP":"1642413265",
            "XLM":"1031647566"
        }
        return msg_map[symbol]

    def withdraw(self, dest, symbol, amount):
        event = "WITHDRAW,%s,%s,%s,%s,%s" % (self.name, dest.name, symbol, amount, dest.deposit_address(symbol))
        if symbol in self.require_deposit_message:
            event += "," + dest.deposit_message(symbol)
        record_event(event)

        if symbol != 'USD':
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

    def order_infos(self, txids):
        assert(len(txids) <= 20)

        return self.query_private('QueryOrders', {'txid':','.join(txids)})['result']

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

    def cancel_all_orders(self, exclude_list=[]):
        for txid,info in self.active_orders().items():
            if txid not in exclude_list:
                record_event("CANCELALL,%s,%s" % (self.name,txid))
                self.cancel(txid)

    def active_orders(self):
        return self.query_private('OpenOrders', {})['result']['open']
