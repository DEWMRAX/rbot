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

        self.symbols = ['TRST','WAVES','BTC','ETH','LTC','MLN','REP','GNT','USDT','XEM','RLC','MAID','AMP','DASH','SC','LBC','BAT','ANT','QRL','BNT','SNT','STORJ','ADX','OMG','QTUM','CVC','BCC','STRAT','SYS','DNT','SALT','RCN','KMD','ARK','XMR','POWR','ZEC','ADA','XRP','LSK','MANA','XLM','NEO','DCR']

        self.markets = self.api.get_markets()

        for market in self.markets:
            uniform_ticker = "%s-%s" % (market['MarketCurrency'], market['BaseCurrency'])
            if market['MarketCurrency'] in self.symbols and market['BaseCurrency'] in self.symbols:
                self.fees[uniform_ticker] = Decimal('0.0025')

    def pair_name(self, market):
        return "%s-%s" % (market.currency, market.token)

    def deposit_address(self, symbol):
        addr_map = {
            "BTC":"1LSpJq8xuMudeMLBSPE5GjJBnpcNus1AHq",
            "WAVES":"3P7iY9aePAUaQff4Np8P1aU5CqXifxY3Rc2",
            "TRST":"0x5ba6b3b16e45914e592eac770bea6339b490f35f",
            "ETH":"0x5ba6b3b16e45914e592eac770bea6339b490f35f",
            "LTC":"LMc2UauKvZh4B6zgWT54RqTWdd4yfBuRig",
            "MLN":"0x5ba6b3b16e45914e592eac770bea6339b490f35f",
            "REP":"0x5ba6b3b16e45914e592eac770bea6339b490f35f",
            "GNT":"0x5ba6b3b16e45914e592eac770bea6339b490f35f",
            "USDT":"1Pek9hn1zGArXgZMssmWqSnMGiD8be15RG",
            "XEM":"ND2JRPQIWXHKAA26INVGA7SREEUMX5QAI6VU7HNR",
            "LUN":"0x5ba6b3b16e45914e592eac770bea6339b490f35f",
            "RLC":"0x5ba6b3b16e45914e592eac770bea6339b490f35f",
            "MAID":"16q5kTApohd2awkEHaysu8hMiSShbLd9bZ",
            "AMP":"1KERtB8VcvRq6eZ2F1UCWbchvjX3gQSVAP",
            "DASH":"XfNCccSz357LTh5qsBXqysZUyUntxfCq3A",
            "SC":"1d1af681cb477939c24aee6854e27eb5018024816b26852d590589fb59dbc34297d1d1ea93c0",
            "LBC":"bE47WiZUDT89LMvLduqzjFwxPAfDqEbCcf",
            "BAT":"0x5ba6b3b16e45914e592eac770bea6339b490f35f",
            "ANT":"0x5ba6b3b16e45914e592eac770bea6339b490f35f",
            "1ST":"0x5ba6b3b16e45914e592eac770bea6339b490f35f",
            "HMQ":"0x5ba6b3b16e45914e592eac770bea6339b490f35f",
            "QRL":"0x5ba6b3b16e45914e592eac770bea6339b490f35f",
            "BNT":"0x5ba6b3b16e45914e592eac770bea6339b490f35f",
            "SNT":"0x5ba6b3b16e45914e592eac770bea6339b490f35f",
            "STORJ":"0x5ba6b3b16e45914e592eac770bea6339b490f35f",
            "ADX":"0x5ba6b3b16e45914e592eac770bea6339b490f35f",
            "OMG":"0x5ba6b3b16e45914e592eac770bea6339b490f35f",
            "QTUM":"QSaPHrUnTfVbjz9kjeijubMbPsizy7V7q4",
            "CVC":"0x5ba6b3b16e45914e592eac770bea6339b490f35f",
            "BCC":"1HQvhvXP8C3K5Rt2yRdmZehcS4yyHB5cLp",
            "STRAT":"Sd2BwBLnQUNMzK2dGhiGxL9Tiyo9H6mpUy",
            "SYS":"SYXwyps7kHQ5JUjQWyFTvCEr2Tih5aYE4P",
            "SALT":"0x5ba6b3b16e45914e592eac770bea6339b490f35f",
            "RCN":"0x5ba6b3b16e45914e592eac770bea6339b490f35f",
            "KMD":"RJzMd6htFrFMs4Nwxfh3ihXSUe4DW3zuPL",
            "ARK":"AMxp8KhKYvCHVky5sszHex7z2TwPsBf9JD",
            "XMR":"463tWEBn5XZJSxLU6uLQnQ2iY9xuNcDbjLSjkn3XAXHCbLrTTErJrBWYgHJQyrCwkNgYvyV3z8zctJLPCZy24jvb3NiTcTJ",
            "POWR":"0x5ba6b3b16e45914e592eac770bea6339b490f35f",
            "ZEC":"t1MbuJfpcY2PhbsUF69vJcaVBY1WnFozVi6",
            "ADA":"DdzFFzCqrht96NX3gW7pDBtBmNjThaLhaE3mf5k9dM8m1qCawPuZAno2ghdVKZKGVozSu1zdWBnVj4H5Zzn6wDDzksh8hUrkMXRoQPCv",
            "XRP":"rPVMhWBsfF9iMXYj3aAzJVkPDTFNSyWdKy",
            "LSK":"2120495817187703L",
            "MANA":"0x5ba6b3b16e45914e592eac770bea6339b490f35f",
            "XLM":"GB6YPGW5JFMMP2QB2USQ33EUWTXVL4ZT5ITUNCY3YKVWOJPP57CANOF3",
            "NEO":"AVVqJ1vuTYLERXtnftNmbfM7xUFFMbyszn",
            "DCR":"DsVn72taPNoYN5V82zRRRCBKyje2Tq1qYV5",
            "DNT":"0x5ba6b3b16e45914e592eac770bea6339b490f35f"
        }

        if symbol in self.require_deposit_message: # only message is returned from api
            return addr_map[symbol]

        addr_result = self.api.get_deposit_address(symbol)
        assert(addr_result['Currency'] == symbol)
        assert(addr_result['Address'] == addr_map[symbol])

        return addr_result['Address']

    def deposit_message(self, symbol):
        msg_map = {
            "XEM":"e1fe9ffbdb40436ebfa",
            "XRP":"1583748774",
            "XLM":"35e4e1816cad4c15860",
            "XMR":"153fa389022049e393808eb7850dafd9c9ca703b800945f9be3d2bc8017fd085"
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
