import itbit
import pair
import decimal

p = pair.pair_factory('BTC','USD')

i = itbit.ItBit()
# print(i.api.get_all_wallets().json()[0]['balances'][0])

i.refresh_balances()
print(i.balance)
print(i.any_open_orders())
i.cancel_all_orders()
print(i.any_open_orders())

print(i.trade_ioc(p, 'sell', decimal.Decimal('6270.423432341'), decimal.Decimal('0.004'), 'test'))
