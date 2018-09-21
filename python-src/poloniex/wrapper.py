from poloniex.api import api
from decimal import *
from exchange import Exchange
from order import Order
from logger import record_event
from fees import FEES
import time
import json

def symbol_from_polo(symbol):
    if symbol == "BCH":
        return "BCC"
    if symbol == "STR":
        return "XLM"
    return symbol

def symbol_to_polo(symbol):
    if symbol == "BCC":
        return "BCH"
    if symbol == "XLM":
        return "STR"
    return symbol

def parse_ticker(ticker):
    a = ticker.split('_')
    return (symbol_from_polo(a[1]), symbol_from_polo(a[0]))

INFO_CACHE_PATH = 'poloniex_info.json'

class Poloniex(Exchange):
    def __init__(self):
        Exchange.__init__(self, "POLO")
        with open("poloniex.keys") as secrets_file:
            secrets = json.load(secrets_file)
            self.tapi = api(bytearray(secrets['key'], 'utf-8'), bytearray(secrets['secret'], 'utf-8'))

        with open(INFO_CACHE_PATH) as f:
            self.tickers = json.loads(f.read())

        self.symbols = ['BTC','ETH','GNT','LTC','REP','USDT','XEM','AMP','DASH','SC','LBC','BCC','ZRX','STRAT','SYS','CVC','OMG','STORJ','XMR','ZEC','XRP','LSK','XLM','DCR','GNO','KNC','BAT']
        for ticker in self.tickers.keys():
            (token, currency) = parse_ticker(ticker)
            if token in self.symbols and currency in self.symbols:
                uniform_ticker = "%s-%s" % (token, currency)
                self.fees[uniform_ticker] = FEES[self.name].taker

    def pair_name(self, pair):
        return "%s_%s" % (symbol_to_polo(pair.currency), symbol_to_polo(pair.token))

    def deposit_address(self, symbol):
        addr_map = {
            "BTC":"1JbhGLW24FWRRPbCDnVu8B1kgFNWaHgq6Z",
            "ETH":"0xb53a989d12df547167494433a0f82db0c8685049",
            "USDT":"1MX92mn6SdRHW42VqkyusAWcpw7mJrs7F6",
            "LTC":"Le8cQjfAkFxCqU1v3LgoiLwqvtaffKdYL3",
            "GNT":"0xd0582307bce51ea75b823526138bcb484dfcfaed",
            "REP":"0x7c76193c43a1b0a4c7a6b7bd85abbb0fd5dae41b",
            "XEM":"NBZMQO7ZPBYNBDUR7F75MAKA2S3DHDCIFG775N3D",
            "AMP":"1PFECM7zAaUx2svsVvdCKixui79Mn7ekUh",
            "DASH":"XdYRotE1AvNBTWgKtWJttsUxy8rbPPJqXh",
            "SC":"538ae6014a5abf2fafda6d3c111fd8d83413ac98f9f8313f0344ba891bde64a6b8268d3f688c",
            "LBC":"bGZiktvzjVRZ9XkCmbJPb2Z4e7iREo4xKn",
            "BCC":"1LBW616GieQL9JcKLiSraE5Pgu85cBWdjk",
            "ZRX":"0x8e4ba814b18775a13e416563bbb306b5700652fd",
            "CVC":"0xe571d5011c3f57c3c82a62793825e0d1ec8b97e6",
            "STRAT":"ScGYRqA7A9nD4iyERBe86BmsFabKcskwrk",
            "SYS":"STcmyMDmyvQJEUtVr7DfqxCqVKWtDhtYqc",
            "STORJ":"0x32cc01288f18c8a9d7c650bec2c1582b4766d4be",
            "XMR":"4JUdGzvrMFDWrUUwY3toJATSeNwjn54LkCnKBPRzDuhzi5vSepHfUckJNxRL2gjkNrSqtCoRUrEDAgRwsQvVCjZbS4TFDq8Urz68nzwMvk",
            "ZEC":"t1NE899bnfzmXkr4fbDcQqX79dyJTK5T1SQ",
            "XRP":"raSrwKu8JqzRR9M7JBoRVw5yVXXu9Ctynj",
            "LSK":"6761288143735703303L",
            "XLM":"GCGNWKCJ3KHRLPM3TM6N7D3W5YKDJFL6A2YCXFXNMRTZ4Q66MEMZ6FI2",
            "DCR":"DsSAaFwT3YTq51eLGcji2w58Dxe7JEr5KPq",
            "GNO":"0x127309f8a73162504e2744abebd0add2c5844b94",
            "OMG":"0x9e5841973e2a3e3636c8b398a4e7a5c0adc53287",
            "KNC":"0x5ea1048e225e33c1094d605f545eceae449145ac",
            "BAT":"0xc9ca4e9271c9b427df344bb527725d1893dd70f7"
        }

        if symbol in ['XEM','XLM']: # only message is returned from api for XEM
            return addr_map[symbol]

        returned_addrs = self.tapi.returnDepositAddresses()
        assert(addr_map[symbol] == returned_addrs[symbol_to_polo(symbol)])

        return addr_map[symbol]

    def deposit_message(self, symbol):
        if symbol in ['XMR','XRP']: # polo does not use payment-id on incoming XMR deposits
            return ""

        msg_map = {
            "XEM":"b4100e259d74b5a7",
            "XLM":"6007798"
        }
        returned_msgs = self.tapi.returnDepositAddresses()
        assert(msg_map[symbol] == returned_msgs[symbol_to_polo(symbol)])

        return msg_map[symbol]

    def withdraw(self, dest, symbol, amount):
        address = dest.deposit_address(symbol)
        message = ""
        event = "WITHDRAW,%s,%s,%s,%s,%s" % (self.name, dest.name, symbol, amount, address)
        if symbol in self.require_deposit_message:
            message = dest.deposit_message(symbol)

        if message:
            event += "," + message
            record_event(event)
            self.tapi.withdraw_message(symbol_to_polo(symbol), amount, address, message)
        else:
            record_event(event)
            self.tapi.withdraw(symbol_to_polo(symbol), amount, address)

    def refresh_balances(self):
        balances = self.tapi.returnBalances()
        for symbol in self.symbols:
            self.balance[symbol] = Decimal(balances[symbol_to_polo(symbol)])

    def trade(self, pair, side, price, amount):
        if (side == "buy"):
            return self.tapi.buy(self.pair_name(pair), price, amount)
        else:
            assert(side == "sell")
            return self.tapi.sell(self.pair_name(pair), price, amount)

    def trade_ioc(self, pair, side, price, amount, reason):
        trade_result = self.trade(pair, side, price, amount)

        filled_qty = amount - Decimal(trade_result[u'amountUnfilled'])

        record_event("EXEC,%s,%s,%s,%s,%s,%0.9f,%0.9f" % (side.upper(), reason, self.name, pair.token, pair.currency, filled_qty, price))

        return filled_qty

    def any_open_orders(self):
        orders = self.tapi.returnOpenOrders("all")
        for market,ordrs in orders.items():
            if ordrs:
                return True

        return False

    def cancel_all_orders(self):
        orders = self.tapi.returnOpenOrders("all")
        for market in orders: # all-open-orders call is segregated by markets
            for order in orders[market]:
                order_number = order[u'orderNumber']
                record_event("CANCELALL,%s,%s" % (self.name,order_number))
                self.tapi.cancel(market, order_number)
