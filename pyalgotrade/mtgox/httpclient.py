# PyAlgoTrade
#
# Copyright 2011-2013 Gabriel Martin Becedillas Ruiz
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
.. moduleauthor:: Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>
"""

import base64
import time
import urllib
import urllib2
import json
import hmac
import hashlib

from pyalgotrade.mtgox import base

class Error(Exception):
    def __init__(self, error, response):
        Exception.__init__(self, error)
        self.__response = response

    def getResponse(self):
        return self.__response

def return_or_fail(response, defaultErrorMessage):
    if response["result"] != "success":
        errorMessage = response.get("error", defaultErrorMessage)
        raise Error(errorMessage, response)
    return response["return"]

# https://en.bitcoin.it/wiki/MtGox/API/HTTP#Python
# https://en.bitcoin.it/wiki/MtGox/API/HTTP/v1
class HTTPClient(object):
    USER_AGENT = "PyAlgoTrade"

    # currency is the account's currency.
    def __init__(self, apiKey, apiSecret, currency):
        self.__apiKey = apiKey
        self.__apiSecret = base64.b64decode(apiSecret)
        self.__currency = currency
        self.__nonce = None
        self.__baseUrl = "https://data.mtgox.com/api/1/"

    def __getNonce(self):
        # nonce must be greater than the last one.
        ret = int(time.time()*1000000)
        if ret == self.__nonce:
            ret += 1
        self.__nonce = ret
        return ret

    def __buildQuery(self, req={}):
        req["nonce"] = self.__getNonce()
        post_data = urllib.urlencode(req)
        headers = {}
        headers["User-Agent"] = HTTPClient.USER_AGENT
        headers["Rest-Key"] = self.__apiKey
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        headers["Rest-Sign"] = base64.b64encode(str(hmac.HMAC(self.__apiSecret, post_data, hashlib.sha512).digest()))
        return (post_data, headers)

    def __sendRequest(self, url, params):
        data, headers = self.__buildQuery(params)
        req = urllib2.Request(url, data, headers)
        response = urllib2.urlopen(req, data)
        return json.loads(response.read())

    def getCurrency(self):
        return self.__currency

    def requestPrivateKeyId(self):
        url = self.__baseUrl + "generic/private/idkey"
        response = self.__sendRequest(url, {})
        return return_or_fail(response, "Failed to retrieve private key id")

    def addOrder(self, orderType, amount, price=None):
        url = self.__baseUrl + "BTC%s/private/order/add" % (self.__currency)
        params = {
            "type": orderType,
            "amount_int": base.to_amount_int(amount)}

        if price is not None:
            params["price_int"] = base.to_value_int(self.__currency, price)
        response = self.__sendRequest(url, params)
        return return_or_fail(response, "Failed to add order")

    def cancelOrder(self, orderId):
        url = self.__baseUrl + "BTC%s/private/order/cancel" % (self.__currency)
        params = {"oid": orderId}
        response = self.__sendRequest(url, params)
        return return_or_fail(response, "Failed to cancel order")

    def privateInfo(self):
        url = self.__baseUrl + "generic/private/info"
        response = self.__sendRequest(url, {})
        return return_or_fail(response, "Failed to retrieve private info")

    def openOrders(self):
        url = self.__baseUrl + "generic/private/orders"
        response = self.__sendRequest(url, {})
        return return_or_fail(response, "Failed to retrieve open orders")
