from collections import namedtuple

Fee = namedtuple('Fee', ['maker','taker'])

FEES = {
    "POLO":Fee(15, 21),
    "KRAKEN":Fee(10, 14),
    "BITTREX":Fee(25, 21),
    "BINANCE":Fee(5, 3),
    "LIQUI":Fee(10, 21),
    "GDAX":Fee(25, 15),
    "ITBIT":Fee(20, 15),
    "BITFLYER":Fee(20, 0)
}
