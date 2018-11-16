import GDAX
import pair
import decimal

p = pair.pair_factory('BCH','USD')

g = GDAX.GDAX()
# g.refresh_balances()
# g.balance
# g.any_open_orders()
# g.cancel_all_orders()

g.trade_ioc(p, 'buy', decimal.Decimal('1619.10'), decimal.Decimal('1.5'), 'test')
