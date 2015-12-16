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

# Coinbase protocol reference: Check https://docs.exchange.coinbase.com/

import logging
logging.getLogger("requests").setLevel(logging.ERROR)

import requests
import pyalgotrade.logger


logger = pyalgotrade.logger.getLogger(__name__)


class OrderBookLevel(object):
    def __init__(self, values):
        self.__values = values

    def getPrice(self):
        return float(self.__values[0])

    def getSize(self):
        return float(self.__values[1])


class OrderBook(object):
    def __init__(self, msgDict):
        self.__msgDict = msgDict

    def getDict(self):
        return self.__msgDict

    def getSequence(self):
        return int(self.__msgDict["sequence"])

    def getBids(self):
        return map(OrderBookLevel, self.__msgDict["bids"])

    def getAsks(self):
        return map(OrderBookLevel, self.__msgDict["asks"])


class HTTPClient(object):
    USER_AGENT = "PyAlgoTrade"
    REQUEST_TIMEOUT = 30

    def __init__(self, url):
        self.__url = url

    def _get(self, path, url_params):
        headers = {}
        headers["User-Agent"] = HTTPClient.USER_AGENT
        headers["Content-Type"] = "application/json"

        url = self.__url + path
        response = requests.get(url, headers=headers, params=url_params, timeout=HTTPClient.REQUEST_TIMEOUT)
        response.raise_for_status()
        return response

    def getOrderBook(self, product, level=1):
        path = "/products/%s/book" % product
        url_params = {
            "level": level
        }
        return OrderBook(self._get(path, url_params).json())
