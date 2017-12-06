from pymongo import MongoClient

from order import Order
from decimal import *

cached_balances = MongoClient().arbot.cached_balances

class Exchange():
    def __init__(self, name):
        self.balance = dict()
        self.fees = dict()
        self.name = name

        self.active = True
        self.permanent_inactive = False

        self.require_deposit_message = ['XEM','XMR']

    def has_pair(self, pair):
        return (str(pair) in self.fees)

    def get_fee(self, pair):
        return self.fees[str(pair)]

    def get_balance(self, symbol):
        if symbol in self.balance:
            return self.balance[symbol]
        else:
            return Decimal(0)

    def initial_refresh_balances(self):
        try:
            self.unprotected_refresh_balances()
        except:
            for doc in cached_balances.find({'exchange':self.name}):
                self.balance[doc['symbol']] = Decimal(doc['balance'])

            self.permanent_inactive = True
            self.active = False

    def protected_refresh_balances(self):
        if self.permanent_inactive:
            return

        try:
            self.unprotected_refresh_balances()
        except:
            for doc in cached_balances.find({'exchange':self.name}):
                self.balance[doc['symbol']] = Decimal(doc['balance'])

            self.active = False

    def unprotected_refresh_balances(self):
        if self.permanent_inactive:
            raise Exception("%s is inactive but requested balance refresh" % self.name)

        self.refresh_balances()

        for symbol in self.balance:
            cached_balances.update({'symbol':symbol}, {'$set':{'exchange':self.name, 'balance':"%d" % self.balance[symbol]}})

        self.active = True
