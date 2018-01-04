from collections import namedtuple

Fee = namedtuple('Fee', ['maker','taker'])

FEES = {
    "POLO":Fee(15, 25),
    "KRAKEN":Fee(10, 20),
    "BITTREX":Fee(25, 25),
    "BINANCE":Fee(5, 5),
    "LIQUI":Fee(10, 25),
    "GDAX":Fee(25, 0)
}
