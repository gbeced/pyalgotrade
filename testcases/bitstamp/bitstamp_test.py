# PyAlgoTrade
#
# Copyright 2011-2018 Gabriel Martin Becedillas Ruiz
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

import datetime
import time
import threading

from six.moves import queue

from testcases import test_strategy

from pyalgotrade.bitstamp import barfeed
from pyalgotrade.bitstamp import broker
from pyalgotrade.bitstamp import wsclient
from pyalgotrade.bitstamp import httpclient
from pyalgotrade.utils import dt


SYMBOL = "BTC"
PRICE_CURRENCY = "USD"
INSTRUMENT = "BTC/USD"


class WebSocketClientThreadMock(threading.Thread):
    def __init__(self, events):
        super(WebSocketClientThreadMock, self).__init__()
        self.__queue = queue.Queue()
        for event in events:
            self.__queue.put(event)
        self.__queue.put((wsclient.WebSocketClient.Event.DISCONNECTED, None))
        self.__stop = False

    def waitInitialized(self, timeout):
        return True

    def getQueue(self):
        return self.__queue

    def start(self):
        threading.Thread.start(self)

    def run(self):
        while not self.__queue.empty() and not self.__stop:
            time.sleep(0.01)

    def stop(self):
        self.__stop = True


class TestingLiveTradeFeed(barfeed.LiveTradeFeed):
    def __init__(self):
        super(TestingLiveTradeFeed, self).__init__([INSTRUMENT])
        # Disable reconnections so the test finishes when ON_DISCONNECTED is pushed.
        self.enableReconection(False)
        self.__events = []
        self.__lastDateTime = None

    def addTrade(self, dateTime, tid, price, amount):
        # To avoid collisions.
        if dateTime == self.__lastDateTime:
            dateTime += datetime.timedelta(microseconds=len(self.__events))
        self.__lastDateTime = dateTime

        eventDict = {
            "data": {
                "id": tid,
                "price": price,
                "amount": amount,
                "microtimestamp": int(dt.datetime_to_timestamp(dateTime) * 1e6),
                "type": 0,
            },
            "channel": "live_trades_btcusd",
        }
        self.__events.append((wsclient.WebSocketClient.Event.TRADE, wsclient.Trade(eventDict)))

    def buildWebSocketClientThread(self):
        return WebSocketClientThreadMock(self.__events)


class HTTPClientMock(object):
    class UserTransactionType:
        MARKET_TRADE = 2

    def __init__(self):
        self.__userTransactions = []
        self.__openOrders = []
        self.__btcAvailable = 0.0
        self.__usdAvailable = 0.0
        self.__nextTxId = 1
        self.__nextOrderId = 1000
        self.__userTransactionsRequested = False

    def setUSDAvailable(self, usd):
        self.__usdAvailable = usd

    def setBTCAvailable(self, btc):
        self.__btcAvailable = btc

    def addOpenOrder(self, orderId, btcAmount, usdAmount):
        jsonDict = {
            'id': orderId,
            'datetime': str(datetime.datetime.now()),
            'type': 0 if btcAmount > 0 else 1,
            'price': str(usdAmount),
            'amount': str(abs(btcAmount)),
            'currency_pair': "BTC/USD",
        }
        self.__openOrders.append(jsonDict)

    def addUserTransaction(self, orderId, btcAmount, usdAmount, fillPrice, fee):
        jsonDict = {
            'btc': str(btcAmount),
            'btc_usd': str(fillPrice),
            'datetime': str(datetime.datetime.now()),
            'fee': str(fee),
            'id': self.__nextTxId,
            'order_id': orderId,
            'type': 2,
            'usd': str(usdAmount)
        }
        self.__userTransactions.insert(0, jsonDict)
        self.__nextTxId += 1

    def getAccountBalance(self):
        jsonDict = {
            'btc_available': str(self.__btcAvailable),
            # 'btc_balance': '0',
            # 'btc_reserved': '0',
            # 'fee': '0.5000',
            'usd_available': str(self.__usdAvailable),
            # 'usd_balance': '0.00',
            # 'usd_reserved': '0'
        }
        return httpclient.AccountBalance(jsonDict)

    def getOpenOrders(self):
        return [httpclient.Order(jsonDict) for jsonDict in self.__openOrders]

    def cancelOrder(self, orderId):
        pass

    def _buildOrder(self, price, amount):
        jsonDict = {
            'id': self.__nextOrderId,
            'datetime': str(datetime.datetime.now()),
            'type': 0 if amount > 0 else 1,
            'price': str(price),
            'amount': str(abs(amount)),
        }
        self.__nextOrderId += 1
        return httpclient.Order(jsonDict)

    def buyLimit(self, currencyPair, limitPrice, quantity):
        assert(quantity > 0)
        return self._buildOrder(limitPrice, quantity)

    def sellLimit(self, currencyPair, limitPrice, quantity):
        assert(quantity > 0)
        return self._buildOrder(limitPrice, quantity)

    def getUserTransactions(self, transactionType=None):
        # The first call is to retrieve user transactions that should have been
        # processed already.
        if not self.__userTransactionsRequested:
            self.__userTransactionsRequested = True
            return []
        else:
            return [httpclient.UserTransaction(jsonDict) for jsonDict in self.__userTransactions]


class TestingLiveBroker(broker.LiveBroker):
    def __init__(self, clientId, key, secret):
        self.__httpClient = HTTPClientMock()
        super(TestingLiveBroker, self).__init__(clientId, key, secret)

    def buildHTTPClient(self, clientId, key, secret):
        return self.__httpClient

    def getHTTPClient(self):
        return self.__httpClient


class TestStrategy(test_strategy.BaseStrategy):
    def __init__(self, feed, brk):
        super(TestStrategy, self).__init__(feed, brk)
        self.bid = None
        self.ask = None

        # Subscribe to order book update events to get bid/ask prices to trade.
        feed.getOrderBookUpdateEvent().subscribe(self.__onOrderBookUpdate)

    def __onOrderBookUpdate(self, orderBookUpdate):
        bid = orderBookUpdate.getBidPrices()[0]
        ask = orderBookUpdate.getAskPrices()[0]

        if bid != self.bid or ask != self.ask:
            self.bid = bid
            self.ask = ask
