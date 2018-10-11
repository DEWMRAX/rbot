from collections import namedtuple
from decimal import *
from order import Order

# targetting ~$2,000 for max_notional
MAX_NOTIONAL={"BTC":Decimal('.2'), "ETH":Decimal('4'), "USDT":Decimal('2000'), "USD":Decimal('2000')}
MIN_NOTIONAL={"BTC":Decimal('.002'), "ETH":Decimal('.04'), "USDT":Decimal('40'), "USD":Decimal('50')}
MIN_QUANTITY={"BTC":Decimal('0.002'), "GNO":Decimal('0.05'), "AION":Decimal('2'), "NANO":Decimal('1000000000'), "PART":Decimal('1000000000'), "ELF":Decimal('1000000000'), "BNB":Decimal('100000000'), "VET":Decimal('2'), "REQ":Decimal('10'), "XRP":Decimal('30'), "LSK":Decimal('0.5'), "MANA":Decimal('10'), "XLM":Decimal('300'), "NEO":Decimal('0.1'), "DCR":Decimal('0.1'), "ADA":Decimal('3'), "ZEC":Decimal('0.03'), "POWR":Decimal('5'), "XMR":Decimal('0.1'), "ARK":Decimal('1'), "RCN":Decimal('20'), "KMD":Decimal('2'), "ENG":Decimal('20'), "AST":Decimal('10'), "SALT":Decimal('.5'), "FUN":Decimal('50'), "KNC":Decimal('3'), "DNT":Decimal('1'), "OAX":Decimal('.01'), "STRAT":Decimal('.01'), "SYS":Decimal('.01'), "ZRX":Decimal('1'), "BCC":Decimal('.01'), "STORJ":Decimal('.01'), "ADX":Decimal('.01'), "OMG":Decimal('.01'), "QTUM":Decimal('.01'), "CVC":Decimal('.01'), "DGD":Decimal('.01'), "QRL":Decimal('.01'), "BNT":Decimal('.01'), "SNGLS":Decimal('.01'), "SNT":Decimal('.01'), "BAT":Decimal('50'), "ANT":Decimal('.01'), "DASH":Decimal('.03'), "SC":Decimal('1'), "LBC":Decimal('0.1'), "TRST":Decimal('0.1'), "WAVES":Decimal('0.1'), "ETH":Decimal('.02'), "GNT":Decimal('0.1'), "ICN":Decimal('2'), "MLN":Decimal('0.1'), "LTC":Decimal('0.1'), "REP":Decimal('0.3'), "BTC":Decimal('0.001'), "XEM":Decimal('0.1'), "RLC":Decimal('0.1'), "AMP":Decimal('0.1')}

class Pair(namedtuple('Pair', ['token','currency','network_friction'])):
    __slots__ = ()
    def __str__(self):
        return "%s-%s" % (self.token, self.currency)

    def __eq__(self, other):
        return str(self) == str(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def max_notional(self):
        return MAX_NOTIONAL[self.currency]

    def min_notional(self):
        return MIN_NOTIONAL[self.currency]

    def min_quantity(self):
        return MIN_QUANTITY[self.token]

    def maker_network_friction(self):
        return Decimal(1) * self.network_friction

def friction(base):
    return Decimal(0.6 * base)

ALL_PAIRS = [

    Pair('XRP', 'BTC', friction(0.005)),
    Pair('XRP', 'ETH', friction(0.005)),

    Pair('MANA', 'BTC', friction(0.007)),
    Pair('MANA', 'ETH', friction(0.007)),

    Pair('XLM', 'BTC', friction(0.004)),
    Pair('XLM', 'ETH', friction(0.004)),

    Pair('ADA', 'BTC', friction(0.004)),
    Pair('ADA', 'ETH', friction(0.004)),

    Pair('XMR', 'BTC', friction(0.007)),
    Pair('XMR', 'ETH', friction(0.007)),

    Pair('RCN', 'BTC', friction(0.009)),
    Pair('RCN', 'ETH', friction(0.007)),

    Pair('ZRX', 'BTC', friction(0.009)),
    Pair('ZRX', 'ETH', friction(0.007)),

    Pair('KNC', 'BTC', friction(0.008)),
    Pair('KNC', 'ETH', friction(0.006)),

    Pair('DNT', 'ETH', friction(0.01)),
    Pair('DNT', 'BTC', friction(0.01)),

    Pair('CVC', 'BTC', friction(0.008)),
    Pair('CVC', 'ETH', friction(0.006)),

    Pair('BAT', 'BTC', friction(0.008)),
    Pair('BAT', 'ETH', friction(0.006)),

    Pair('LTC', 'BTC', friction(0.008)),
    Pair('ETH', 'BTC', friction(0.006)),

    Pair('BCC', 'BTC', friction(0.008)),
    Pair('BCC', 'ETH', friction(0.006)),

    Pair('BTC', 'USD', friction(0.003)),
    Pair('LTC', 'USD', friction(0.002)),
    Pair('ETH', 'USD', friction(0.002)),
    Pair('BCC', 'USD', friction(0.002)),
    Pair('XRP', 'USD', friction(0.002)),

    Pair('BNB', 'BTC', friction(10000)),
    Pair('PART', 'BTC', friction(10000)),
]

ALL_SYMBOLS=['USD','BTC','ETH','LTC','BCC','XRP','XLM','XMR','ADA','BAT','CVC','ZRX','KNC','RCN','MANA','BNB','DNT','PART']

pair_map = dict()

for pair in ALL_PAIRS:
    pair_map[str(pair)] = pair

def pair_factory(token, currency):
    token = token.upper()
    currency = currency.upper()
    return pair_map.get("%s-%s" % (token, currency))
