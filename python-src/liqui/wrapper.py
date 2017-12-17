import liqui
from decimal import *
from exchange import Exchange
from order import Order
from logger import record_event
import time

class Liqui(Exchange):
    def __init__(self):
        Exchange.__init__(self, "LIQUI")
        self.conn = liqui.connection
        handler = liqui.KeyHandler("liqui.keys", resaveOnDeletion=True)
        self.tapi = liqui.TradeAPI(handler.getKeys()[0], handler)

        self.prices = {}

        self.symbols = ['BTC','ETH','GNT','ICN','LTC','MLN','REP','USDT','TRST','WAVES','EDG','RLC','DASH','MYST','BAT','ANT','QRL','BNT','PTOY','SNGLS','SNT','MCO','STORJ','ADX','OMG','CVC','DGD','BCC','ZRX','DNT','OAX','KNC','SALT','ENG','AST','REQ','MANA']

        self.tickers = liqui.common.market_info

        for ticker,info in self.tickers['pairs'].items():
            (token, currency) = ticker.upper().split('_')
            uniform_ticker = "%s-%s" % (token, currency)
            if token in self.symbols and currency in self.symbols:
                self.fees[uniform_ticker] = Decimal(info[u'fee']) * Decimal('0.01')

    def pair_name(self, market):
        return "%s_%s" % (market.token.lower(), market.currency.lower())

    def deposit_address(self, symbol):
        return {
            "BTC":"1GHEMS5syrGmcCpARx81iddcFM253Y15cK",
            "ETH":"0xed631591f77bc43539606e7e7f1110ea4f821f02",
            "USDT":"18cFBUBHVxPDP2eydEQ5wfezFZHwpbsBUd",
            "LTC":"LUMfsUsNnm6o6r4XhE3Cfhk6x7YTzwAzGW",
            "GNT":"0xed631591f77bc43539606e7e7f1110ea4f821f02",
            "REP":"0xed631591f77bc43539606e7e7f1110ea4f821f02",
            "MLN":"0xed631591f77bc43539606e7e7f1110ea4f821f02",
            "ICN":"0xed631591f77bc43539606e7e7f1110ea4f821f02",
            "TRST":"0xed631591f77bc43539606e7e7f1110ea4f821f02",
            "WAVES":"3PMgCcb5ZHQ54seUzAowQyyC8rJ1xPYQAoY",
            "EDG":"0xed631591f77bc43539606e7e7f1110ea4f821f02",
            "RLC":"0xed631591f77bc43539606e7e7f1110ea4f821f02",
            "DASH":"Xsk3d6UnT2UPFckdEoJjfkyh1a1PkQh1MQ",
            "MYST":"0xed631591f77bc43539606e7e7f1110ea4f821f02",
            "BAT":"0xed631591f77bc43539606e7e7f1110ea4f821f02",
            "ANT":"0xed631591f77bc43539606e7e7f1110ea4f821f02",
            "QRL":"0xed631591f77bc43539606e7e7f1110ea4f821f02",
            "BNT":"0xed631591f77bc43539606e7e7f1110ea4f821f02",
            "PTOY":"0xed631591f77bc43539606e7e7f1110ea4f821f02",
            "SNGLS":"0xed631591f77bc43539606e7e7f1110ea4f821f02",
            "SNT":"0xed631591f77bc43539606e7e7f1110ea4f821f02",
            "MCO":"0xed631591f77bc43539606e7e7f1110ea4f821f02",
            "STORJ":"0xed631591f77bc43539606e7e7f1110ea4f821f02",
            "ADX":"0xed631591f77bc43539606e7e7f1110ea4f821f02",
            "OMG":"0xed631591f77bc43539606e7e7f1110ea4f821f02",
            "CVC":"0xed631591f77bc43539606e7e7f1110ea4f821f02",
            "DGD":"0xed631591f77bc43539606e7e7f1110ea4f821f02",
            "BCC":"12jHw8UidA4ByN1ZFeg1wVDidzLi368zua",
            "ZRX":"0xed631591f77bc43539606e7e7f1110ea4f821f02",
            "DNT":"0xed631591f77bc43539606e7e7f1110ea4f821f02",
            "OAX":"0xed631591f77bc43539606e7e7f1110ea4f821f02",
            "SALT":"0xed631591f77bc43539606e7e7f1110ea4f821f02",
            "ENG":"0xed631591f77bc43539606e7e7f1110ea4f821f02",
            "AST":"0xed631591f77bc43539606e7e7f1110ea4f821f02",
            "REQ":"0xed631591f77bc43539606e7e7f1110ea4f821f02",
            "MANA":"0xed631591f77bc43539606e7e7f1110ea4f821f02",
            "KNC":"0xed631591f77bc43539606e7e7f1110ea4f821f02"
        }[symbol]

    def withdraw(self, dest, symbol, amount):
        record_event("WITHDRAW,%s,%s,%s,%s,%s" % (self.name, dest.name, symbol, amount, dest.deposit_address(symbol)))

    def refresh(self, market):
        (asks, bids) = liqui.getDepth(self.pair_name(market), connection=self.conn)
        self.bids[str(market)] = map(self.parse_order, bids)
        self.asks[str(market)] = map(self.parse_order, asks)

    def refresh_balances(self):
        info = self.tapi.getInfo(connection=self.conn)
        self.open_orders = info.open_orders

        for ticker in self.symbols:
            self.balance[ticker] = Decimal(getattr(info, "balance_%s" % ticker.lower()))

    def trade(self, market, side, price, amount):
        return self.tapi.trade(self.pair_name(market), side, price, amount, connection=self.conn)

    def trade_ioc(self, market, side, price, amount, reason):
        order = self.tapi.trade(self.pair_name(market), side, price, amount, connection=self.conn)

        filled_qty = amount

        if order.remains: # deal with a partial fill
            self.cancel(order)

            order_info = self.order_info(order)
            assert(order_info.status != 0)

            filled_qty = order_info.start_amount - order_info.amount

        record_event("EXEC,%s,%s,%s,%s,%s,%0.9f,%0.9f" % (side.upper(), reason, self.name, market.token, market.currency, filled_qty, price))

        return filled_qty

    def cancel(self, order):
        return self.tapi.cancelOrder(order.order_id, connection=self.conn)

    def order_info(self, order):
        return self.tapi.orderInfo(order.order_id, connection=self.conn)

    def any_open_orders(self):
        return self.open_orders > 0

    def cancel_all_orders(self):
        for order in self.active_orders():
            record_event("CANCELALL,%s,%s" % (self.name,order.order_id))
            self.cancel(order)

    def active_orders(self):
        return self.tapi.activeOrders(connection=self.conn)
