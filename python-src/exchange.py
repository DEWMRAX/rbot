from order import Order
from decimal import *

class Exchange():
    def __init__(self, name):
        self.balance = dict()
        self.fees = dict()
        self.name = name

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
