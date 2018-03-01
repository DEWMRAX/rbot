import KUCOIN
import pair
import decimal
import time

p = pair.pair_factory('BCC','BTC')

k = KUCOIN.KuCoin()
# k.refresh_balances()
# print k.deposit_address('BCC')
# print k.deposit_address('NEO')
time.sleep(2)
k.api.create_order(p, 'BUY', '0.001', '0.001')

# g.any_open_orders()
# g.cancel_all_orders()

# g.trade_ioc(p, 'buy', decimal.Decimal('1619.10'), decimal.Decimal('1.5'), 'test')
#
# import kraken
# import pair
# from decimal import Decimal
# k = kraken.Kraken()
# p = pair.pair_factory('BTC','USD')
# k.lot_decimals['BTC-USD']
# k.trade_ioc(p, 'buy', Decimal('10900'), Decimal('0.01'), 'test')
