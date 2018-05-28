from decimal import *
from exchange import Exchange
from logger import record_event
from fees import FEES
from binance.api import api
import json

def pair_name_to_binance(pair):
    p = pair.split('-')
    return "%s%s" % (p[0], p[1])

PAIRS = dict()
INFO_CACHE_PATH = 'binance_info.json'
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
    for pair_info in info['symbols']:
        if pair_info['status'] != 'TRADING':
            continue

        for filtr in pair_info['filters']:
            if filtr['filterType'] == 'PRICE_FILTER':
                price_decimals = convert_tick_size_to_decimal_position(filtr['tickSize'])
            elif filtr['filterType'] == 'LOT_SIZE':
                lot_decimals = convert_tick_size_to_decimal_position(filtr['stepSize'])

        PAIRS["%s-%s" % (pair_info['baseAsset'],pair_info['quoteAsset'])] = {
            'price_decimals':price_decimals,
            'lot_decimals':lot_decimals
        }

class Binance(Exchange):
    def __init__(self):
        Exchange.__init__(self, 'BINANCE')

        with open('binance.keys', 'r') as api_key:
            self.api = api(api_key.readline().strip(), api_key.readline().strip())

        self.symbols = ['BTC','ETH','USDT','LTC','BNT','OAX','SNT','DNT','QTUM','ICN','OMG','ZRX','STRAT','SNGLS','KNC','FUN','SALT','DASH','ENG','AST','STORJ','RCN','KMD','ARK','XMR','BCC','POWR','ZEC','BAT','ADA','ADX','DGD','REQ','XRP','LSK','MANA','XLM','NEO','BNB','VEN','ELF','RLC','AION','NANO','XEM','CVC']
        self.fees = {}

        account_info = self.api.account_info()

        for ticker in PAIRS:
            self.fees[ticker] = FEES[self.name].taker

    def pair_name(self, pair):
        return "%s%s" % (pair.token.upper(), pair.currency.upper())

    def deposit_address(self, symbol):
        address = {
            "ETH":"0xbaf143b074bb657e85daafdf33419d74f23c4335",
            "OAX":"0xbaf143b074bb657e85daafdf33419d74f23c4335",
            "SNT":"0xbaf143b074bb657e85daafdf33419d74f23c4335",
            "DNT":"0xbaf143b074bb657e85daafdf33419d74f23c4335",
            "QTUM":"QQr8rugKwibQ5crpEL6UKhbsn6qtyiyhap",
            "ICN":"0xbaf143b074bb657e85daafdf33419d74f23c4335",
            "BTC":"1Mag9UBm59C3SELgNaJaWCW6NvKK67bWVt",
            "USDT":"14zD8kuh6SrqBMPrrHgSKvSKgH58ZNXq5p",
            "LTC":"LeYHKBF35xp9zW9ErswveBnPhsEBEbSTZY",
            "BNT":"0xbaf143b074bb657e85daafdf33419d74f23c4335",
            "ZRX":"0xbaf143b074bb657e85daafdf33419d74f23c4335",
            "OMG":"0xbaf143b074bb657e85daafdf33419d74f23c4335",
            "STRAT":"SbSrjKFQfuqqurgudA3LykXcaTi7n5k4QP",
            "SNGLS":"0xbaf143b074bb657e85daafdf33419d74f23c4335",
            "KNC":"0xbaf143b074bb657e85daafdf33419d74f23c4335",
            "SALT":"0xbaf143b074bb657e85daafdf33419d74f23c4335",
            "ENG":"0xbaf143b074bb657e85daafdf33419d74f23c4335",
            "AST":"0xbaf143b074bb657e85daafdf33419d74f23c4335",
            "RCN":"0xbaf143b074bb657e85daafdf33419d74f23c4335",
            "KMD":"RBav4CAzqFb7YoHPYHnar4p4VBd3bpEsFt",
            "STORJ":"0xbaf143b074bb657e85daafdf33419d74f23c4335",
            "DASH":"XjsmifTUttg82woe6Pz34rcqiroCehpVSz",
            "ARK":"ANmGwvAqD9yHT3bVo4Xp4BcvHCzwcoioNC",
            "XMR":"44tLjmXrQNrWJ5NBsEj2R77ZBEgDa3fEe9GLpSf2FRmhexPvfYDUAB7EXX1Hdb3aMQ9FLqdJ56yaAhiXoRsceGJCRS3Jxkn",
            "BCC":"1Mag9UBm59C3SELgNaJaWCW6NvKK67bWVt",
            "POWR":"0xbaf143b074bb657e85daafdf33419d74f23c4335",
            "ZEC":"t1MF9S9o7jhEGVSSgfW7oFupBEohgBTxpvE",
            "BAT":"0xbaf143b074bb657e85daafdf33419d74f23c4335",
            "ADA":"DdzFFzCqrhtC4qrBx2nPuvWF6YKn1jbYpqasmH8uKVJgYZFkpRTFtKVm1UmvhDTAukeqS7yxCGjAXNMb7RQU9xKCsLTiL1mYQs6ngJ1f",
            "FUN":"0xbaf143b074bb657e85daafdf33419d74f23c4335",
            "ADX":"0xbaf143b074bb657e85daafdf33419d74f23c4335",
            "REQ":"0xbaf143b074bb657e85daafdf33419d74f23c4335",
            "XRP":"rEb8TK3gBgk5auZkwc6sHnwrGVJH8DuaLh",
            "LSK":"1646977822985505651L",
            "MANA":"0xbaf143b074bb657e85daafdf33419d74f23c4335",
            "XLM":"GAHK7EEG2WWHVKDNT4CEQFZGKF2LGDSW2IVM4S5DP42RBW3K6BTODB4A",
            "NEO":"AWcMmdvUBoJ6MmStNR91X2Q7Xne3VxchRe",
            "XEM":"NC64UFOWRO6AVMWFV2BFX2NT6W2GURK2EOX6FFMZ",
            "VEN":"0xbaf143b074bb657e85daafdf33419d74f23c4335",
            "RLC":"0xbaf143b074bb657e85daafdf33419d74f23c4335",
            "AION":"0xbaf143b074bb657e85daafdf33419d74f23c4335",
            "CVC":"0xbaf143b074bb657e85daafdf33419d74f23c4335",
            "DGD":"0xbaf143b074bb657e85daafdf33419d74f23c4335"
        }[symbol]

        assert(address == self.api.deposit_address(symbol))

        return address

    def deposit_message(self, symbol):
        msg_map = {
            "XMR":"416aedb4b063c03e4c078aaf2f45807ccc3dc4f2143c4fd67a9d35b1959ce128",
            "XRP":"100077456",
            "XLM":"1034493707",
            "XEM":"101028584"
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
            print "BINANCE TAGGED WITHDRAWAL"
            print self.api.withdraw_tag(symbol, amount, address, message, key_name)
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
