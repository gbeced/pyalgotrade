# PyAlgoTrade
#
# Copyright 2011-2015 Gabriel Martin Becedillas Ruiz
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

import time
import datetime
import hmac
import hashlib
import requests
import threading

from pyalgotrade.utils import dt
from pyalgotrade.bitstamp import common

import logging
logging.getLogger("requests").setLevel(logging.ERROR)


def parse_datetime(dateTime):
    try:
        ret = datetime.datetime.strptime(dateTime, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        ret = datetime.datetime.strptime(dateTime, "%Y-%m-%d %H:%M:%S.%f")
    return dt.as_utc(ret)


class AccountBalance(object):
    def __init__(self, jsonDict):
        self.__jsonDict = jsonDict

    def getDict(self):
        return self.__jsonDict

    def getAvailableCurrency(self, currency="USD"):
        return float(self.__jsonDict["{}_available".format(currency.lower())])

    def getUSDAvailable(self):
        # deprecated
        return self.getAvailableCurrency("USD")

    def getBTCAvailable(self):
        # deprecated
        return self.getAvailableCurrency("BTC")


class Order(object):
    def __init__(self, jsonDict):
        self.__jsonDict = jsonDict

    def getDict(self):
        return self.__jsonDict

    def getId(self):
        return int(self.__jsonDict["id"])

    def isBuy(self):
        return self.__jsonDict["type"] == 0

    def isSell(self):
        return self.__jsonDict["type"] == 1

    def getPrice(self):
        return float(self.__jsonDict["price"])

    def getAmount(self):
        return float(self.__jsonDict["amount"])

    def getDateTime(self):
        return parse_datetime(self.__jsonDict["datetime"])


class UserTransaction(object):
    def __init__(self, jsonDict):
        self.__jsonDict = jsonDict

    def getDict(self):
        return self.__jsonDict

    def getCurrency(self, currency="BTC"):
        return float(self.__jsonDict[currency.lower()])

    def getCurrencyPairPrice(self, currency1="BTC", currency2="USD"):
        return float(self.__jsonDict["{}_{}".format(currency1.lower(), currency2.lower())])

    def getBTC(self):
        # deprecated
        return self.getCurrency("BTC")

    def getBTCUSD(self):
        # deprecated
        return self.getCurrencyPairPrice("BTC", "USD")

    def getDateTime(self):
        return parse_datetime(self.__jsonDict["datetime"])

    def getFee(self):
        return float(self.__jsonDict["fee"])

    def getId(self):
        return int(self.__jsonDict["id"])

    def getOrderId(self):
        return int(self.__jsonDict["order_id"])

    def getUSD(self):
        # deprecated
        return self.getCurrency("USD")


class HTTPClient(object):
    USER_AGENT = "PyAlgoTrade"
    REQUEST_TIMEOUT = 30

    class UserTransactionType:
        MARKET_TRADE = 2

    def __init__(self, clientId, key, secret):
        self.__clientId = clientId
        self.__key = key
        self.__secret = secret
        self.__prevNonce = None
        self.__lock = threading.Lock()

    def _getNonce(self):
        ret = int(time.time())
        if ret == self.__prevNonce:
            ret += 1
        self.__prevNonce = ret
        return ret

    def _buildQuery(self, params):
        # Build the signature.
        nonce = self._getNonce()
        message = "%d%s%s" % (nonce, self.__clientId, self.__key)
        signature = hmac.new(self.__secret, msg=message, digestmod=hashlib.sha256).hexdigest().upper()

        # Headers
        headers = {}
        headers["User-Agent"] = HTTPClient.USER_AGENT

        # POST data.
        data = {}
        data.update(params)
        data["key"] = self.__key
        data["signature"] = signature
        data["nonce"] = nonce

        return (data, headers)

    def _post(self, url, params):
        common.logger.debug("POST to %s with params %s" % (url, str(params)))

        # Serialize access to nonce generation and http requests to avoid
        # sending them in the wrong order.
        with self.__lock:
            data, headers = self._buildQuery(params)
            response = requests.post(url, headers=headers, data=data, timeout=HTTPClient.REQUEST_TIMEOUT)
            response.raise_for_status()

        jsonResponse = response.json()

        # Check for errors.
        if isinstance(jsonResponse, dict):
            error = jsonResponse.get("error")
            if error is not None:
                raise Exception(error)

        return jsonResponse

    def getAccountBalance(self):
        url = "https://www.bitstamp.net/api/v2/balance/"
        jsonResponse = self._post(url, {})
        return AccountBalance(jsonResponse)

    def getOpenOrders(self):
        url = "https://www.bitstamp.net/api/v2/open_orders/all"
        jsonResponse = self._post(url, {})
        return [Order(json_open_order) for json_open_order in jsonResponse]

    def cancelOrder(self, orderId):
        url = "https://www.bitstamp.net/api/cancel_order/"
        params = {"id": orderId}
        jsonResponse = self._post(url, params)
        if jsonResponse != True:
            raise Exception("Failed to cancel order")

    def buyLimit(self, limitPrice, quantity, currency="USD", instrument="BTC"):
        url = "https://www.bitstamp.net/api/v2/buy/{}/".format(common.available_pairs[currency][instrument].lower())

        # Rounding price to avoid 'Ensure that there are no more than 2 decimal places'
        # error.
        price = round(limitPrice, 2)
        # Rounding amount to avoid 'Ensure that there are no more than 8 decimal places'
        # error.
        amount = round(quantity, 8)

        params = {
            "price": price,
            "amount": amount
        }
        jsonResponse = self._post(url, params)
        return Order(jsonResponse)

    def sellLimit(self, limitPrice, quantity, currency="USD", instrument="BTC"):
        url = "https://www.bitstamp.net/api/v2/sell/{}/".format(common.available_pairs[currency][instrument].lower())

        # Rounding price to avoid 'Ensure that there are no more than 2 decimal places'
        # error.
        price = round(limitPrice, 2)
        # Rounding amount to avoid 'Ensure that there are no more than 8 decimal places'
        # error.
        amount = round(quantity, 8)

        params = {
            "price": price,
            "amount": amount
        }
        jsonResponse = self._post(url, params)
        return Order(jsonResponse)

    def getUserTransactions(self, transactionType=None):
        url = "https://www.bitstamp.net/api/v2/user_transactions/"
        jsonResponse = self._post(url, {})
        if transactionType is not None:
            jsonUserTransactions = filter(
                lambda jsonUserTransaction: jsonUserTransaction["type"] == transactionType, jsonResponse
            )
        else:
            jsonUserTransactions = jsonResponse
        return [UserTransaction(jsonUserTransaction) for jsonUserTransaction in jsonUserTransactions]
