from bittrex.api import api
from decimal import *
from exchange import Exchange
from order import Order
from logger import record_event
import json
import time

class Bittrex(Exchange):
    def __init__(self):
        Exchange.__init__(self, "BITTREX")
        with open("bittrex.keys") as secrets_file:
            secrets = json.load(secrets_file)
            self.api = api(secrets['key'], secrets['secret'])

        self.symbols = ['TRST','WAVES','BTC','ETH','LTC','MLN','REP','GNT','USDT','XEM','RLC','MAID','AMP','DASH','SC','LBC','BAT','ANT','QRL','BNT','SNT','STORJ','ADX','OMG','QTUM','CVC','BCC','STRAT','SYS','FUN','DNT','SALT','RCN','KMD','ARK','XMR','POWR','ZEC','ADA','XRP','LSK','MANA','XLM','NEO','DCR']

        self.markets = self.api.get_markets()

        for market in self.markets:
            uniform_ticker = "%s-%s" % (market['MarketCurrency'], market['BaseCurrency'])
            if market['MarketCurrency'] in self.symbols and market['BaseCurrency'] in self.symbols:
                self.fees[uniform_ticker] = Decimal('0.0025')

    def pair_name(self, market):
        return "%s-%s" % (market.currency, market.token)

    def deposit_address(self, symbol):
        addr_map = {
            "BTC":"12VP4fy8Hzr1DhJtEyTYgxT4m97fmoCHGc",
            "WAVES":"3PPercZ2N4RaEcgWGE3ppFeDZzwxxJ4jLWU",
            "INCNT":"3P3CEauB4vwJNfCdpkYzCFXvr5iz7N1z1T7",
            "TRST":"0xccf4d4848b96476f6c448160fb085c7f6c5cc188",
            "ETH":"0xccf4d4848b96476f6c448160fb085c7f6c5cc188",
            "LTC":"LSFhS1A2RG34AgXd8PMUD3XBqM9G1shfPY",
            "MLN":"0xccf4d4848b96476f6c448160fb085c7f6c5cc188",
            "REP":"0xccf4d4848b96476f6c448160fb085c7f6c5cc188",
            "GNT":"0xccf4d4848b96476f6c448160fb085c7f6c5cc188",
            "USDT":"1PbG9Z11fZPzsX6Q4LymjYSPsgpdu8qpZz",
            "XEM":"ND2JRPQIWXHKAA26INVGA7SREEUMX5QAI6VU7HNR",
            "LUN":"0xccf4d4848b96476f6c448160fb085c7f6c5cc188",
            "RLC":"0xccf4d4848b96476f6c448160fb085c7f6c5cc188",
            "MAID":"1FeLyz5jZLN9V1ZoABJGm1qBvTSt6FbTn6",
            "AMP":"1HRi8Na67FgJSBjQkvLHrax9H3Fr8WcZgh",
            "DASH":"XeUKacotW9k4azRT6ryuFNQihyptpbRVV9",
            "SC":"e19692e310176b4d80fafc90dd17a16e525bd7dfd6215c91cd67ab4068c99f7e1920a04844e9",
            "LBC":"bJiieHLhhSayAXQAHNXcKJF2XC1oELg9Wd",
            "BAT":"0xccf4d4848b96476f6c448160fb085c7f6c5cc188",
            "ANT":"0xccf4d4848b96476f6c448160fb085c7f6c5cc188",
            "1ST":"0xccf4d4848b96476f6c448160fb085c7f6c5cc188",
            "HMQ":"0xccf4d4848b96476f6c448160fb085c7f6c5cc188",
            "QRL":"0xccf4d4848b96476f6c448160fb085c7f6c5cc188",
            "BNT":"0xccf4d4848b96476f6c448160fb085c7f6c5cc188",
            "SNT":"0xccf4d4848b96476f6c448160fb085c7f6c5cc188",
            "STORJ":"0xccf4d4848b96476f6c448160fb085c7f6c5cc188",
            "ADX":"0xccf4d4848b96476f6c448160fb085c7f6c5cc188",
            "OMG":"0xccf4d4848b96476f6c448160fb085c7f6c5cc188",
            "QTUM":"QbDy528rVZFKGWQUpvSkiDMFm49P7LZLV6",
            "CVC":"0xccf4d4848b96476f6c448160fb085c7f6c5cc188",
            "BCC":"1JbhFhk9guXyZuiYWJo1wVsNNPwenguhFn",
            "STRAT":"SVkyfcMzo3VJxCaA5WjoG4nJLNTeWh44tf",
            "SYS":"SNHvSbxWxjG8qvSjsaqzVajjQRHpJgZRi3",
            "FUN":"0xccf4d4848b96476f6c448160fb085c7f6c5cc188",
            "SALT":"0xccf4d4848b96476f6c448160fb085c7f6c5cc188",
            "RCN":"0xccf4d4848b96476f6c448160fb085c7f6c5cc188",
            "KMD":"RFm1kynPjs1iU4UepVTNtzdcMWie1QJZHC",
            "ARK":"AeajBvW8LfZiCRtbPdx5usZStL4cdWqquo",
            "XMR":"463tWEBn5XZJSxLU6uLQnQ2iY9xuNcDbjLSjkn3XAXHCbLrTTErJrBWYgHJQyrCwkNgYvyV3z8zctJLPCZy24jvb3NiTcTJ",
            "POWR":"0xccf4d4848b96476f6c448160fb085c7f6c5cc188",
            "ZEC":"t1QSuLHGXwpvTTScYDWWUKRARTJpLFa6UH1",
            "ADA":"DdzFFzCqrhsnjhEeVLtdyjvJuS95C4p7kb61zsu2zKXypmEqegtbi9ny7z2fjdtLFkkcy9fzxvZPek9M5eDvMMg8Us8Fjnoj5QGDtRmp",
            "XRP":"rPVMhWBsfF9iMXYj3aAzJVkPDTFNSyWdKy",
            "LSK":"11955598195039745432L",
            "MANA":"0xccf4d4848b96476f6c448160fb085c7f6c5cc188",
            "XLM":"GB6YPGW5JFMMP2QB2USQ33EUWTXVL4ZT5ITUNCY3YKVWOJPP57CANOF3",
            "NEO":"Abg4CcBGzixsebjfmiKWpvyh6pbfYc2FrL",
            "DCR":"Dsa9UDLMw2VeGsKxaSZMV4Q6wDuHQB2C5ck",
            "DNT":"0xccf4d4848b96476f6c448160fb085c7f6c5cc188"
        }

        if symbol in self.require_deposit_message: # only message is returned from api
            return addr_map[symbol]

        addr_result = self.api.get_deposit_address(symbol)
        assert(addr_result['Currency'] == symbol)
        assert(addr_result['Address'] == addr_map[symbol])

        return addr_result['Address']

    def deposit_message(self, symbol):
        msg_map = {
            "XEM":"1cdb8c71c28542f3a27",
            "XRP":"1276454630",
            "XLM":"5bbf3951cb0e4c59af8",
            "XMR":"e0474c83ba4244bbab5ce22538afea5db78963079cf54aeead92a02872b25969"
        }

        msg_result = self.api.get_deposit_address(symbol)
        assert(msg_result['Currency'] == symbol)
        assert(msg_result['Address'] == msg_map[symbol])

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
            self.api.withdraw_message(symbol, amount, address, message)
        else:
            record_event(event)
            self.api.withdraw(symbol, amount, address)

    def refresh_balances(self):
        for info in self.api.get_balances():
            if info['Currency'] in self.symbols:
                self.balance[info['Currency']] = Decimal(info['Available'])

    def trade_ioc(self, market, side, price, amount, reason):
        if side == 'buy':
            order_id = self.api.buy_limit(self.pair_name(market), amount, price)['uuid']
        else:
            order_id = self.api.sell_limit(self.pair_name(market), amount, price)['uuid']

        order_info = self.api.get_order(order_id)
        print order_info

        if order_info['QuantityRemaining'] == 0:
            filled_qty = Decimal(order_info['Quantity'])

        else:
            if not order_info['Closed']:
                time.sleep(3)
                self.api.cancel(order_id)

            print 'second print'
            order_info = self.api.get_order(order_id)
            print order_info

            assert(order_info['Closed'])

            filled_qty = Decimal(order_info['Quantity'] - order_info['QuantityRemaining'])

        average_price = 0
        if 'PricePerUnit' in order_info and order_info['PricePerUnit'] is not None:
            average_price = order_info['PricePerUnit']

        record_event("EXEC,%s,%s,%s,%s,%s,%0.9f,%0.9f" % (side.upper(), reason, self.name, market.token, market.currency, filled_qty, average_price))

        return filled_qty

    def any_open_orders(self):
        return len(self.api.get_open_orders()) > 0

    def cancel_all_orders(self):
        for order in self.api.get_open_orders():
            record_event("CANCELALL,%s,%s" % (self.name,order['OrderUuid']))
            self.api.cancel(order['OrderUuid'])
