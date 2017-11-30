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

        self.symbols = ['EDG','TRST','WAVES','BTC','ETH','LTC','MLN','REP','GNT','USDT','FCT','XEM','RLC','MAID','AMP','DASH','SC','LBC','MYST','BAT','ANT','WINGS','TIME','GUP','TKN','QRL','BNT','PTOY','CFI','SNGLS','SNT','MCO','STORJ','ADX','PAY','OMG','QTUM','CVC','DGD','BCC','STRAT','SYS','GNO','FUN','DNT','SALT','MTL','RCN','KMD','ARK','XMR','POWR','ZEC','ADA']

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
            "TRST":"0xc1938b09db973739098d4afd9ebe45e539b60d29",
            "EDG":"0xad878233c39a74c6e6b248d9fca8cb2b7cf3c24b",
            "ETH":"0xe034bcf55701d4ba643c79637036f3de794225cb",
            "LTC":"LSFhS1A2RG34AgXd8PMUD3XBqM9G1shfPY",
            "MLN":"0xb9b54c03e36200d7ab0f12e66cdc4e37d7972ef7",
            "REP":"0x2073ea7de92efcc4fa50f8da5e95b0b6f761da67",
            "GNT":"0x9673282d255b24fddf1f20056efd64f60dcead3a",
            "USDT":"1PbG9Z11fZPzsX6Q4LymjYSPsgpdu8qpZz",
            "FCT":"FA2RA1t4iy9eskH5wdm3m1f2oqJb3DKV4PwQh9qRrHi4uDTMkR9P",
            "XEM":"ND2JRPQIWXHKAA26INVGA7SREEUMX5QAI6VU7HNR",
            "LUN":"0xa63866d33cf3b520a0e1585d6e090ef0db06d424",
            "RLC":"0xebe2ec0bd6ee1a60c06bc7d19a9a09ff9468c983",
            "MAID":"1FeLyz5jZLN9V1ZoABJGm1qBvTSt6FbTn6",
            "AMP":"1HRi8Na67FgJSBjQkvLHrax9H3Fr8WcZgh",
            "DASH":"XeUKacotW9k4azRT6ryuFNQihyptpbRVV9",
            "SC":"e19692e310176b4d80fafc90dd17a16e525bd7dfd6215c91cd67ab4068c99f7e1920a04844e9",
            "LBC":"bJiieHLhhSayAXQAHNXcKJF2XC1oELg9Wd",
            "MYST":"0xf10a1951b291344d610def7a37691e5134ee1202",
            "BAT":"0x9be2499f084bf1d77529db53746256c71be2fc62",
            "ANT":"0xe443971e4dde9e8cf3837c1ff8942f6ba2e65bbc",
            "1ST":"0x08489cbde7352162d46027a61abb3700abc01b89",
            "WINGS":"0x44d366a45540eed0a3e8bac18f542ccc650a40cc",
            "TIME":"0xb4de521d7a2ab9f080661c3e722e1c626e95ee6e",
            "GUP":"0x764d3dd9410d2d515027619a5a5dab40eb7fa8af",
            "TKN":"0x373f35b67f48f97bf061b2be5176d059f167ffad",
            "HMQ":"0x684a5c9af9e0400bce47eafb9169a373f18455c2",
            "QRL":"0xe23c1001e05d0a7d115bc322bd9cf9b548e1d7d5",
            "BNT":"0x4c37e79d6735a3f3993b8c137c043a52ef8f2c86",
            "PTOY":"0x704dfefd38404751b37528178fe8038c327567d7",
            "CFI":"0x98b0fcd96610bf9d0e9ec0c1fc587ff97831f3a3",
            "SNGLS":"0x418684cfe6bcba5d1bf27e17271778097bac451a",
            "SNT":"0x90bb6c2cf13761d3071365ca1ada85387eb31569",
            "MCO":"0x0bf450a1729474605f45e8b582209a8c291d7cef",
            "STORJ":"0xe59f7d8149c8836caf8c13b8f71cb3765bd008e4",
            "ADX":"0xdc53401db51d306c3995f2b15d5f821a33ae119c",
            "PAY":"0x46d1f80c8ea9ddb4f30b962ac8781e446e829231",
            "OMG":"0xb75484c5c4456ccc9ace88ca79d98ed38c1e0c38",
            "QTUM":"QbDy528rVZFKGWQUpvSkiDMFm49P7LZLV6",
            "CVC":"0x77a8586078cf6f21f4c93b55f98134d6b1ab4500",
            "DGD":"0x8f59c61955f2155a43cda71342f42788d8401e1a",
            "BCC":"1JbhFhk9guXyZuiYWJo1wVsNNPwenguhFn",
            "GNO":"0xccf4d4848b96476f6c448160fb085c7f6c5cc188",
            "STRAT":"SVkyfcMzo3VJxCaA5WjoG4nJLNTeWh44tf",
            "SYS":"SNHvSbxWxjG8qvSjsaqzVajjQRHpJgZRi3",
            "FUN":"0x4a10875dce29877c383f308e0c120937ba5bb41f",
            "SALT":"0x7f1971f94af46c902ce979a425a0e575ffbea426",
            "MTL":"0x2da3b3601826defd0e5e19f551ac537a85772b3d",
            "RCN":"0xe01598aaa7f328f7e80abfdf358e8bfc21bd738a",
            "KMD":"RFm1kynPjs1iU4UepVTNtzdcMWie1QJZHC",
            "ARK":"AeajBvW8LfZiCRtbPdx5usZStL4cdWqquo",
            "XMR":"463tWEBn5XZJSxLU6uLQnQ2iY9xuNcDbjLSjkn3XAXHCbLrTTErJrBWYgHJQyrCwkNgYvyV3z8zctJLPCZy24jvb3NiTcTJ",
            "POWR":"0x2393e05d634cdee5d099a49be4750a2c6a9d9d73",
            "ZEC":"t1QSuLHGXwpvTTScYDWWUKRARTJpLFa6UH1",
            "ADA":"DdzFFzCqrhsnjhEeVLtdyjvJuS95C4p7kb61zsu2zKXypmEqegtbi9ny7z2fjdtLFkkcy9fzxvZPek9M5eDvMMg8Us8Fjnoj5QGDtRmp",
            "DNT":"0xc2fb8a5e120dc566893544530d51131f84b4677f"
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
