# Copyright (c) 2013-2015 Alan McIntyre

import decimal
import httplib
import json
import re
import os

INFO_CACHE_PATH = 'liqui_info.json'

class InvalidTradePairException(Exception):
    """ Exception raised when an invalid pair is passed. """
    pass


class InvalidTradeTypeException(Exception):
    """ Exception raise when invalid trade type is passed. """
    pass


class InvalidTradeAmountException(Exception):
    """ Exception raised if trade amount is too much or too little. """
    pass


class APIResponseError(Exception):
    """ Exception raise if the API replies with an HTTP code
    not in the 2xx range. """
    pass

def parseJSONResponse(response):
    def parse_decimal(var):
        return decimal.Decimal(var)

    try:
        r = json.loads(response, parse_float=parse_decimal,
                       parse_int=parse_decimal)
    except Exception as e:
        msg = "Error while attempting to parse JSON response:" \
              " %s\nResponse:\n%r" % (e, response)
        raise Exception(msg)

    return r


HEADER_COOKIE_RE = re.compile(r'__cfduid=([a-f0-9]{46})')
BODY_COOKIE_RE = re.compile(r'document\.cookie="a=([a-f0-9]{32});path=/;";')


class BTCEConnection:
    def __init__(self, apiDomain, timeout=30):
        self.apiDomain = apiDomain
        self._timeout = timeout
        self.setup_connection()

    def setup_connection(self):
        if ("HTTPS_PROXY" in os.environ):
          match = re.search(r'http://([\w.]+):(\d+)',os.environ['HTTPS_PROXY'])
          if match:
            self.conn = httplib.HTTPSConnection(match.group(1),
                                                port=match.group(2),
                                                timeout=self._timeout)
          self.conn.set_tunnel(self.apiDomain)
        else:
          self.conn = httplib.HTTPSConnection(self.apiDomain, timeout=self._timeout)
        self.cookie = None

    def close(self):
        self.conn.close()

    def getCookie(self):
        self.cookie = ""

        try:
            self.conn.request("GET", '/')
            response = self.conn.getresponse()
        except Exception:
            # reset connection so it doesn't stay in a weird state if we catch
            # the error in some other place
            self.conn.close()
            self.setup_connection()
            raise

        setCookieHeader = response.getheader("Set-Cookie")
        match = HEADER_COOKIE_RE.search(setCookieHeader)
        if match:
            self.cookie = "__cfduid=" + match.group(1)

        match = BODY_COOKIE_RE.search(response.read())
        if match:
            if self.cookie != "":
                self.cookie += '; '
            self.cookie += "a=" + match.group(1)

    def makeRequest(self, url, extra_headers=None, params="", with_cookie=False):
        headers = {"Content-type": "application/x-www-form-urlencoded"}
        if extra_headers is not None:
            headers.update(extra_headers)

        if with_cookie:
            if self.cookie is None:
                self.getCookie()

            headers.update({"Cookie": self.cookie})

        try:
            self.conn.request("POST", url, params, headers)
            response = self.conn.getresponse()

            if response.status < 200 or response.status > 299:
                msg = "API response error: %s".format(response.status)
                raise APIResponseError(msg)
        except Exception:
            # reset connection so it doesn't stay in a weird state if we catch
            # the error in some other place
            self.conn.close()
            self.setup_connection()
            raise

        return response.read()

    def makeJSONRequest(self, url, extra_headers=None, params=""):
        response = self.makeRequest(url, extra_headers, params)
        return parseJSONResponse(response)

def validatePair(pair):
    if pair not in all_pairs:
        if "_" in pair:
            a, b = pair.split("_", 1)
            swapped_pair = "%s_%s" % (b, a)
            if swapped_pair in all_pairs:
                msg = "Unrecognized pair: %r (did you mean %s?)"
                msg = msg % (pair, swapped_pair)
                raise InvalidTradePairException(msg)
        raise InvalidTradePairException("Unrecognized pair: %r" % pair)


def validateOrder(pair, trade_type, rate, amount):
    validatePair(pair)
    if trade_type not in ("buy", "sell"):
        raise InvalidTradeTypeException("Unrecognized trade type: %r" % trade_type)

    minimum_amount = min_orders[pair]
    formatted_min_amount = formatCurrency(minimum_amount, pair)
    if amount < minimum_amount:
        msg = "Trade amount %r too small; should be >= %s" % \
              (amount, formatted_min_amount)
        raise InvalidTradeAmountException(msg)


def truncateAmountDigits(value, digits):
    quantum = exps[digits]
    if type(value) is float:
        value = str(value)
    if type(value) is str:
        value = decimal.Decimal(value)
    return value.quantize(quantum)


def truncateAmount(value, pair):
    return truncateAmountDigits(value, max_digits[pair])


def formatCurrencyDigits(value, digits):
    s = str(truncateAmountDigits(value, digits))
    s = s.rstrip("0")
    if s[-1] == ".":
        s = "%s0" % s

    return s

def formatCurrency(value, pair):
    return formatCurrencyDigits(value, max_digits[pair])




decimal.getcontext().rounding = decimal.ROUND_DOWN
exps = [decimal.Decimal("1e-%d" % i) for i in range(16)]

connection = BTCEConnection("api.liqui.io", timeout=60)
with open(INFO_CACHE_PATH) as f:
    market_info = json.loads(f.read())

all_currencies = []
all_pairs = []
max_digits = {}
min_orders = {}
for ticker, info in market_info['pairs'].items():
    all_pairs.append(str(ticker))
    max_digits[str(ticker)] = int(info['decimal_places'])
    min_orders[str(ticker)] = info['min_amount']
    (token, currency) = ticker.split('_')
    if currency not in all_currencies:
        all_currencies.append(str(currency))
    if token not in all_currencies:
        all_currencies.append(str(token))

all_pairs = tuple(all_pairs)
all_currencies = tuple(all_currencies)
