from pymongo import MongoClient

from order import Order
from decimal import *
from logger import record_event

cached_balances = MongoClient().arbot.cached_balances

NO_INACTIVE = ['KRAKEN']

class Exchange():
    def __init__(self, name):
        self.balance = dict()
        self.fees = dict()
        self.name = name

        self.active = True
        self.permanent_inactive = False

        self.require_deposit_message = ['XEM','XMR','XRP','XLM']

    def has_pair(self, pair):
        return (pair.token in self.symbols and pair.currency in self.symbols and str(pair) in self.fees)

    def get_fee(self, pair):
        return self.fees[str(pair)]

    def get_maker_fee(self, pair):
        assert(str(pair) in self.fees)
        return FEES[self.name].maker

    def get_balance(self, symbol):
        if symbol in self.balance:
            return self.balance[symbol]
        else:
            return Decimal(0)

    def protected_any_open_orders(self):
        if self.active:
            return self.any_open_orders()
        else:
            return False

    def protected_cancel_all_orders(self):
        if self.active:
            return self.cancel_all_orders()
        else:
            return False

    def initial_refresh_balances(self):
        try:
            self.unprotected_refresh_balances()
        except Exception as e:
            if self.name in NO_INACTIVE:
                raise(e)

            for doc in cached_balances.find({'exchange':self.name}):
                if doc['symbol'] in self.symbols:
                    self.balance[doc['symbol']] = Decimal(doc['balance'])

            record_event("PERM_INACTIVE,%s" % self.name)
            self.permanent_inactive = True
            self.active = False

    def protected_refresh_balances(self):
        if self.permanent_inactive:
            return

        try:
            self.unprotected_refresh_balances()
        except Exception as e:
            if self.name in NO_INACTIVE:
                raise(e)

            for doc in cached_balances.find({'exchange':self.name}):
                self.balance[doc['symbol']] = Decimal(doc['balance'])

            record_event("INACTIVE,%s" % self.name)
            self.active = False

    def unprotected_refresh_balances(self):
        if self.permanent_inactive:
            raise Exception("%s is inactive but requested balance refresh" % self.name)

        self.refresh_balances()

        for symbol in self.balance:
            cached_balances.update({'symbol':symbol, 'exchange':self.name}, {'$set':{'balance':"%0.8f" % self.balance[symbol]}}, upsert=True)

        self.active = True
