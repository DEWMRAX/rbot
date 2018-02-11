import bitflyer
import pair
import decimal
import time

p = pair.pair_factory('BTC','USD')

bf = bitflyer.BitFlyer()
# print(bf.api.getbalance())
#
# print(bf.any_open_orders())
# bf.cancel_all_orders()
# time.sleep(1)
# print(bf.any_open_orders())
#
print(bf.trade_ioc(p, 'buy', decimal.Decimal('9000'), decimal.Decimal('0.003'), 'test'))
# bf.refresh_balances()

# print(bf.api.getchildorders(product_code='BTC_USD', child_order_acceptance_id='JRF20180211-165237-444034'))

# print(bf.trade_ioc(p, 'sell', decimal.Decimal('6270.423432341'), decimal.Decimal('0.004'), 'test'))
