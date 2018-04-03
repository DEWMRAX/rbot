import time
import requests
import hmac
from hashlib import sha256
try:
    from urllib import urlencode
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urlencode
    from urllib.parse import urljoin

def full_url(s):
    return "https://www.binance.com/api/v3/%s" % s

def wapi_url(s, q):
    return "https://www.binance.com/wapi/v3/%s.html?%s" % (s, q)

class api(object):
    def __init__(self, api_key, api_secret):
        self.key = api_key
        self.secret = api_secret.encode('utf-8')

    def private(self, method, options=None):
        if not options:
            options = {}
        options['timestamp'] = int(time.time() * 1000)

        query_string = urlencode(options)
        signature = hmac.new(self.secret, query_string.encode('UTF-8'), sha256).hexdigest()
        query_string += "&signature=" + signature

        headers={'X-MBX-APIKEY': self.key}

        if method in ['account', 'openOrders']:
            return requests.get(
                full_url("%s?%s" % (method, query_string)),
                headers=headers
            ).json()

        if method == 'deleteOrder':
            return requests.delete(
                full_url("order?%s" % query_string),
                headers=headers
            ).json()

        if method == 'newOrder':
            return requests.post(
                full_url("order?%s" % query_string),
                headers=headers
            ).json()

        if method == 'queryOrder':
            return requests.get(
                full_url("order?%s" % query_string),
                headers=headers
            ).json()

        if method == 'withdraw':
            return requests.post(
                wapi_url(method, query_string),
                headers=headers
            ).json()

        if method == 'depositAddress':
            return requests.get(
                wapi_url(method, query_string),
                headers=headers
            ).json()

        raise Exception()

    def account_info(self):
        return self.private('account')

    def withdraw(self, asset, amount, address, name):
        return self.private('withdraw', {'asset':asset, 'amount':amount, 'address':address, 'name':name})

    def withdraw_tag(self, asset, amount, address, tag, name):
        return self.private('withdraw', {'asset':asset, 'amount':amount, 'address':address, 'addressTag':tag, 'name':name})

    def deposit_address(self, asset):
        return self.private('depositAddress', {'asset':asset})['address']

    def get_orderbook(self, ticker):
        return requests.get(full_url("depth?symbol=%s" % ticker)).json()

    def open_orders(self, ticker):
        return self.private('openOrders', {'symbol':ticker})

    def cancel_order(self, order):
        return self.private('deleteOrder', {'symbol':order['symbol'], 'orderId':order['orderId']})

    def order_info(self, order):
        return self.private('queryOrder', {'symbol':order['symbol'], 'orderId':order['orderId']})

    def new_order(self, side, ticker, price, quantity):
        return self.private('newOrder', {
            'symbol': ticker,
            'side': side,
            'type': 'LIMIT',
            'timeInForce': 'IOC',
            'quantity' :quantity,
            'price': price
        })
