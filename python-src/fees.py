from collections import namedtuple
from decimal import Decimal

class Fee():
    def __init__(self, maker, taker):
        self.maker = Decimal(maker) / Decimal(10000)
        self.taker = Decimal(maker) / Decimal(10000)

FEES = {
    "POLO":Fee(15, 25),
    "KRAKEN":Fee(6, 16),
    "BITTREX":Fee(25, 25),
    "BINANCE":Fee(5, 5),
    "LIQUI":Fee(10, 25),
    "GDAX":Fee(0, 25),
    "ITBIT":Fee(0, 20),
    "BITFLYER":Fee(0, 0)
}
