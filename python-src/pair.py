from collections import namedtuple
from decimal import *
from order import Order

# targetting ~$2,000 for max_notional
MAX_NOTIONAL={"BTC":Decimal('.2'), "ETH":Decimal('4'), "USDT":Decimal('2000')}
MIN_NOTIONAL={"BTC":Decimal('.002'), "ETH":Decimal('.04'), "USDT":Decimal('5')}
MIN_QUANTITY={"ZEC":Decimal('0.01'), "POWR":Decimal('10'), "XMR":Decimal('0.02'), "ARK":Decimal('1'), "RCN":Decimal('20'), "KMD":Decimal('2'), "ENG":Decimal('4'), "AST":Decimal('10'), "MTL":Decimal('.3'), "SALT":Decimal('.5'), "FUN":Decimal('50'), "SNM":Decimal('10'), "KNC":Decimal('3'), "DNT":Decimal('1'), "OAX":Decimal('.01'), "STRAT":Decimal('.01'), "GNO":Decimal('.01'), "SYS":Decimal('.01'), "ZRX":Decimal('1'), "BCC":Decimal('.01'), "MCO":Decimal('.01'), "STORJ":Decimal('.01'), "ADX":Decimal('.01'), "PAY":Decimal('.01'), "OMG":Decimal('.01'), "QTUM":Decimal('.01'), "CVC":Decimal('.01'), "DGD":Decimal('.01'), "WINGS":Decimal('.01'), "TIME":Decimal('.01'), "GUP":Decimal('.01'), "TKN":Decimal('.01'), "QRL":Decimal('.01'), "BNT":Decimal('.01'), "PTOY":Decimal('.01'), "CFI":Decimal('.01'), "SNGLS":Decimal('.01'), "SNT":Decimal('.01'), "MYST":Decimal('.01'), "BAT":Decimal('.01'), "ANT":Decimal('.01'), "DASH":Decimal('.01'), "SC":Decimal('1'), "LBC":Decimal('0.1'), "EDG":Decimal('0.1'), "TRST":Decimal('0.1'), "WAVES":Decimal('0.1'), "ETH":Decimal('.01'), "GNT":Decimal('0.1'), "ICN":Decimal('2'), "MLN":Decimal('0.1'), "LTC":Decimal('0.1'), "REP":Decimal('0.3'), "BTC":Decimal('0.001'), "FCT":Decimal('0.1'), "XEM":Decimal('0.1'), "RLC":Decimal('0.1'), "MAID":Decimal('0.1'), "AMP":Decimal('0.1')}

class Pair(namedtuple('Pair', ['token','currency','network_friction'])):
    __slots__ = ()
    def __str__(self):
        return "%s-%s" % (self.token, self.currency)

    def max_notional(self):
        return MAX_NOTIONAL[self.currency]

    def min_notional(self):
        return MIN_NOTIONAL[self.currency]

    def min_quantity(self):
        return MIN_QUANTITY[self.token]

def friction(base):
    return Decimal(1.8 * base)

ALL_PAIRS = [
    Pair('ZEC', 'BTC', friction(0.007)),
    Pair('ZEC', 'ETH', friction(0.007)),
    Pair('ZEC', 'USDT', friction(0.008)),

    Pair('POWR', 'BTC', friction(0.0011)),
    Pair('POWR', 'ETH', friction(0.008)),

    Pair('XMR', 'BTC', friction(0.006)),
    Pair('XMR', 'ETH', friction(0.006)),
    Pair('XMR', 'USDT', friction(0.007)),

    Pair('ARK', 'BTC', friction(0.008)),

    Pair('RCN', 'BTC', friction(0.009)),
    Pair('RCN', 'ETH', friction(0.007)),
    Pair('KMD', 'BTC', friction(0.012)),
    Pair('KMD', 'ETH', friction(0.009)),

    Pair('ENG', 'BTC', friction(0.012)),
    Pair('ENG', 'ETH', friction(0.009)),
    Pair('AST', 'BTC', friction(0.012)),
    Pair('AST', 'ETH', friction(0.009)),
    Pair('MTL', 'BTC', friction(0.009)),
    Pair('MTL', 'ETH', friction(0.007)),

    Pair('SALT', 'BTC', friction(0.009)),
    Pair('SALT', 'ETH', friction(0.007)),
    Pair('SNM', 'BTC', friction(0.012)),
    Pair('SNM', 'ETH', friction(0.009)),
    Pair('FUN', 'BTC', friction(0.008)),
    Pair('FUN', 'ETH', friction(0.006)),

    Pair('KNC', 'BTC', friction(0.008)),
    Pair('KNC', 'ETH', friction(0.006)),

    Pair('DNT', 'ETH', friction(0.01)),
    Pair('OAX', 'ETH', friction(0.01)),

    Pair('GNO', 'BTC', friction(0.009)),
    Pair('GNO', 'ETH', friction(0.006)),
    Pair('ZRX', 'BTC', friction(0.008)),
    Pair('ZRX', 'ETH', friction(0.006)),
    Pair('MCO', 'BTC', friction(0.01)),
    Pair('MCO', 'ETH', friction(0.007)),
    Pair('STORJ', 'BTC', friction(0.008)),
    Pair('STORJ', 'ETH', friction(0.006)),
    Pair('ADX', 'BTC', friction(0.01)),
    Pair('ADX', 'ETH', friction(0.007)),
    Pair('PAY', 'BTC', friction(0.01)),
    Pair('PAY', 'ETH', friction(0.007)),
    Pair('OMG', 'BTC', friction(0.01)),
    Pair('OMG', 'ETH', friction(0.007)),
    Pair('QTUM', 'BTC', friction(0.008)),
    Pair('QTUM', 'ETH', friction(0.006)),
    Pair('CVC', 'BTC', friction(0.008)),
    Pair('CVC', 'ETH', friction(0.006)),
    Pair('DGD', 'BTC', friction(0.01)),
    Pair('DGD', 'ETH', friction(0.007)),

    Pair('WINGS', 'BTC', friction(0.01)),
    Pair('WINGS', 'ETH', friction(0.007)),
    Pair('TIME', 'BTC', friction(0.01)),
    Pair('TIME', 'ETH', friction(0.007)),
    Pair('GUP', 'BTC', friction(0.01)),
    Pair('GUP', 'ETH', friction(0.007)),
    Pair('TKN', 'BTC', friction(0.01)),
    Pair('TKN', 'ETH', friction(0.007)),
    Pair('QRL', 'BTC', friction(0.01)),
    Pair('QRL', 'ETH', friction(0.007)),
    Pair('BNT', 'BTC', friction(0.008)),
    Pair('BNT', 'ETH', friction(0.006)),
    Pair('PTOY', 'BTC', friction(0.01)),
    Pair('PTOY', 'ETH', friction(0.007)),
    Pair('CFI', 'BTC', friction(0.01)),
    Pair('CFI', 'ETH', friction(0.007)),
    Pair('SNGLS', 'BTC', friction(0.008)),
    Pair('SNGLS', 'ETH', friction(0.006)),
    Pair('SNT', 'BTC', friction(0.01)),
    Pair('SNT', 'ETH', friction(0.007)),

    Pair('MYST', 'BTC', friction(0.008)),
    Pair('MYST', 'ETH', friction(0.006)),
    Pair('BAT', 'BTC', friction(0.008)),
    Pair('BAT', 'ETH', friction(0.006)),
    Pair('ANT', 'BTC', friction(0.01)),
    Pair('ANT', 'ETH', friction(0.007)),

    Pair('SC', 'BTC', friction(0.015)), # SC transfers constantly bugged
    Pair('LBC', 'BTC', friction(0.01)),

    Pair('STRAT', 'BTC', friction(0.07)),
    Pair('SYS', 'BTC', friction(0.07)),

    Pair('MAID', 'BTC', friction(0.02)), # these friction points are asymmetric
    Pair('AMP', 'BTC', friction(0.014)),

    Pair('RLC', 'BTC', friction(0.01)),
    Pair('RLC', 'ETH', friction(0.007)),
    Pair('EDG', 'BTC', friction(0.01)),
    Pair('EDG', 'ETH', friction(0.007)),
    Pair('TRST', 'BTC', friction(0.008)),
    Pair('TRST', 'ETH', friction(0.006)),

    Pair('ICN', 'BTC', friction(0.01)),
    Pair('ICN', 'ETH', friction(0.007)),
    Pair('MLN', 'BTC', friction(0.01)),
    Pair('MLN', 'ETH', friction(0.007)),
    Pair('REP', 'BTC', friction(0.01)),
    Pair('REP', 'ETH', friction(0.007)),
    Pair('GNT', 'BTC', friction(0.008)),
    Pair('GNT', 'ETH', friction(0.006)),

    Pair('WAVES', 'BTC', friction(0.01)),
    Pair('FCT', 'BTC', friction(0.015)), # often withdrawal problems
    Pair('XEM', 'BTC', friction(0.009)),

    Pair('LTC', 'BTC', friction(0.008)),
    Pair('ETH', 'BTC', friction(0.006)),
    Pair('DASH', 'BTC', friction(0.007)),
    Pair('DASH', 'ETH', friction(0.005)),
    Pair('BCC', 'BTC', friction(0.008)),
    Pair('BCC', 'ETH', friction(0.006)),

    Pair('BTC', 'USDT', friction(0.012)),
    Pair('ETH', 'USDT', friction(0.012)),
    Pair('LTC', 'USDT', friction(0.012)),
    Pair('DASH', 'USDT', friction(0.012)),
    Pair('BCC', 'USDT', friction(0.014)),
]

ALL_SYMBOLS=['BTC','ETH','GNT','ICN','LTC','MLN','REP','USDT','TRST','WAVES','EDG','FCT','XEM','RLC','MAID','AMP','DASH','SC','LBC','MYST','BAT','ANT','WINGS','TIME','GUP','TKN','QRL','BNT','PTOY','CFI','SNGLS','SNT','MCO','STORJ','ADX','PAY','OMG','QTUM','CVC','DGD','BCC','ZRX','STRAT','SYS','GNO','DNT','OAX','KNC','FUN','SNM','SALT','ENG','AST','MTL','RCN','KMD','ARK','XMR','POWR','ZEC']

pair_map = dict()

for pair in ALL_PAIRS:
    pair_map[str(pair)] = pair

def pair_factory(token, currency):
    token = token.upper()
    currency = currency.upper()
    return pair_map.get("%s-%s" % (token, currency))
