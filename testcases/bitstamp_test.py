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

import datetime
import time
import threading
import Queue
import json

import common as tc_common
import test_strategy

from pyalgotrade import broker as basebroker
from pyalgotrade.bitstamp import barfeed
from pyalgotrade.bitstamp import broker
from pyalgotrade.bitstamp import wsclient
from pyalgotrade.bitstamp import httpclient
from pyalgotrade.bitstamp import common
from pyalgotrade.bitcoincharts import barfeed as btcbarfeed
from pyalgotrade import strategy
from pyalgotrade import dispatcher


class WebSocketClientThreadMock(threading.Thread):
    def __init__(self, events):
        threading.Thread.__init__(self)
        self.__queue = Queue.Queue()
        self.__queue.put((wsclient.WebSocketClient.ON_CONNECTED, None))
        for event in events:
            self.__queue.put(event)
        self.__queue.put((wsclient.WebSocketClient.ON_DISCONNECTED, None))
        self.__stop = False

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
        barfeed.LiveTradeFeed.__init__(self)
        # Disable reconnections so the test finishes when ON_DISCONNECTED is pushed.
        self.enableReconection(False)
        self.__events = []

    def addTrade(self, dateTime, tid, price, amount):
        dataDict = {
            "id": tid,
            "price": price,
            "amount": amount,
            "type": 0,
            }
        eventDict = {}
        eventDict["data"] = json.dumps(dataDict)
        self.__events.append((wsclient.WebSocketClient.ON_TRADE, wsclient.Trade(dateTime, eventDict)))

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

    def buyLimit(self, limitPrice, quantity):
        assert(quantity > 0)
        return self._buildOrder(limitPrice, quantity)

    def sellLimit(self, limitPrice, quantity):
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
        broker.LiveBroker.__init__(self, clientId, key, secret)

    def buildHTTPClient(self, clientId, key, secret):
        return self.__httpClient

    def getHTTPClient(self):
        return self.__httpClient


class TestStrategy(test_strategy.BaseTestStrategy):
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


class InstrumentTraitsTestCase(tc_common.TestCase):
    def testInstrumentTraits(self):
        traits = common.BTCTraits()
        self.assertEquals(traits.roundQuantity(0), 0)
        self.assertEquals(traits.roundQuantity(1), 1)
        self.assertEquals(traits.roundQuantity(1.1 + 1.1 + 1.1), 3.3)
        self.assertEquals(traits.roundQuantity(1.1 + 1.1 + 1.1 - 3.3), 0)
        self.assertEquals(traits.roundQuantity(0.00441376), 0.00441376)
        self.assertEquals(traits.roundQuantity(0.004413764), 0.00441376)


class BacktestingTestCase(tc_common.TestCase):
    def testBitcoinChartsFeed(self):

        class TestStrategy(strategy.BaseStrategy):
            def __init__(self, feed, brk):
                strategy.BaseStrategy.__init__(self, feed, brk)
                self.pos = None

            def onBars(self, bars):
                if not self.pos:
                    self.pos = self.enterLongLimit("BTC", 5.83, 1, True)

        barFeed = btcbarfeed.CSVTradeFeed()
        barFeed.addBarsFromCSV(tc_common.get_data_file_path("bitstampUSD.csv"))
        brk = broker.BacktestingBroker(100, barFeed)
        strat = TestStrategy(barFeed, brk)
        strat.run()
        self.assertEquals(strat.pos.getShares(), 1)
        self.assertEquals(strat.pos.entryActive(), False)
        self.assertEquals(strat.pos.isOpen(), True)
        self.assertEquals(strat.pos.getEntryOrder().getAvgFillPrice(), 5.83)

    def testMinTrade(self):
        class TestStrategy(strategy.BaseStrategy):
            def __init__(self, feed, brk):
                strategy.BaseStrategy.__init__(self, feed, brk)
                self.pos = None

            def onBars(self, bars):
                if not self.pos:
                    self.pos = self.enterLongLimit("BTC", 4.99, 1, True)

        barFeed = btcbarfeed.CSVTradeFeed()
        barFeed.addBarsFromCSV(tc_common.get_data_file_path("bitstampUSD.csv"))
        brk = broker.BacktestingBroker(100, barFeed)
        strat = TestStrategy(barFeed, brk)
        with self.assertRaisesRegexp(Exception, "Trade must be >= 5"):
            strat.run()


class PaperTradingTestCase(tc_common.TestCase):
    def testBuyWithPartialFill(self):

        class Strategy(TestStrategy):
            def __init__(self, feed, brk):
                TestStrategy.__init__(self, feed, brk)
                self.pos = None

            def onBars(self, bars):
                if self.pos is None:
                    self.pos = self.enterLongLimit("BTC", 100, 1, True)

        barFeed = TestingLiveTradeFeed()
        barFeed.addTrade(datetime.datetime(2000, 1, 1), 1, 100, 0.1)
        barFeed.addTrade(datetime.datetime(2000, 1, 2), 1, 100, 0.1)
        barFeed.addTrade(datetime.datetime(2000, 1, 2), 1, 101, 10)
        barFeed.addTrade(datetime.datetime(2000, 1, 3), 1, 100, 0.2)

        brk = broker.PaperTradingBroker(1000, barFeed)
        strat = Strategy(barFeed, brk)
        strat.run()

        self.assertTrue(strat.pos.isOpen())
        self.assertEquals(round(strat.pos.getShares(), 3), 0.3)
        self.assertEquals(len(strat.posExecutionInfo), 1)
        self.assertEquals(strat.pos.getEntryOrder().getSubmitDateTime().date(), wsclient.get_current_datetime().date())

    def testBuyAndSellWithPartialFill1(self):

        class Strategy(TestStrategy):
            def __init__(self, feed, brk):
                TestStrategy.__init__(self, feed, brk)
                self.pos = None

            def onBars(self, bars):
                if self.pos is None:
                    self.pos = self.enterLongLimit("BTC", 100, 1, True)
                elif bars.getDateTime() == datetime.datetime(2000, 1, 3):
                    self.pos.exitLimit(101)

        barFeed = TestingLiveTradeFeed()
        barFeed.addTrade(datetime.datetime(2000, 1, 1), 1, 100, 0.1)
        barFeed.addTrade(datetime.datetime(2000, 1, 2), 1, 100, 0.1)
        barFeed.addTrade(datetime.datetime(2000, 1, 2), 1, 101, 10)
        barFeed.addTrade(datetime.datetime(2000, 1, 3), 1, 100, 0.2)
        barFeed.addTrade(datetime.datetime(2000, 1, 4), 1, 100, 0.2)
        barFeed.addTrade(datetime.datetime(2000, 1, 5), 1, 101, 0.2)

        brk = broker.PaperTradingBroker(1000, barFeed)
        strat = Strategy(barFeed, brk)
        strat.run()

        self.assertTrue(strat.pos.isOpen())
        self.assertEquals(round(strat.pos.getShares(), 3), 0.1)
        self.assertEquals(len(strat.posExecutionInfo), 1)
        self.assertEquals(strat.pos.getEntryOrder().getSubmitDateTime().date(), wsclient.get_current_datetime().date())
        self.assertEquals(strat.pos.getExitOrder().getSubmitDateTime().date(), wsclient.get_current_datetime().date())

    def testBuyAndSellWithPartialFill2(self):

        class Strategy(TestStrategy):
            def __init__(self, feed, brk):
                TestStrategy.__init__(self, feed, brk)
                self.pos = None

            def onBars(self, bars):
                if self.pos is None:
                    self.pos = self.enterLongLimit("BTC", 100, 1, True)
                elif bars.getDateTime() == datetime.datetime(2000, 1, 3):
                    self.pos.exitLimit(101)

        barFeed = TestingLiveTradeFeed()
        barFeed.addTrade(datetime.datetime(2000, 1, 1), 1, 100, 0.1)
        barFeed.addTrade(datetime.datetime(2000, 1, 2), 1, 100, 0.1)
        barFeed.addTrade(datetime.datetime(2000, 1, 2), 1, 101, 10)
        barFeed.addTrade(datetime.datetime(2000, 1, 3), 1, 100, 0.2)
        barFeed.addTrade(datetime.datetime(2000, 1, 4), 1, 100, 0.2)
        barFeed.addTrade(datetime.datetime(2000, 1, 5), 1, 101, 0.2)
        barFeed.addTrade(datetime.datetime(2000, 1, 6), 1, 102, 5)

        brk = broker.PaperTradingBroker(1000, barFeed)
        strat = Strategy(barFeed, brk)
        strat.run()

        self.assertFalse(strat.pos.isOpen())
        self.assertEquals(strat.pos.getShares(), 0)
        self.assertEquals(len(strat.posExecutionInfo), 2)
        self.assertEquals(strat.pos.getEntryOrder().getSubmitDateTime().date(), wsclient.get_current_datetime().date())
        self.assertEquals(strat.pos.getExitOrder().getSubmitDateTime().date(), wsclient.get_current_datetime().date())

    def testRoundingBugWithTrades(self):
        # Unless proper rounding is in place 0.01 - 0.00441376 - 0.00445547 - 0.00113077 == 6.50521303491e-19
        # instead of 0.

        class Strategy(TestStrategy):
            def __init__(self, feed, brk):
                TestStrategy.__init__(self, feed, brk)
                self.pos = None

            def onBars(self, bars):
                if self.pos is None:
                    self.pos = self.enterLongLimit("BTC", 1000, 0.01, True)
                elif self.pos.entryFilled() and not self.pos.getExitOrder():
                    self.pos.exitLimit(1000, True)

        barFeed = TestingLiveTradeFeed()
        barFeed.addTrade(datetime.datetime(2000, 1, 1), 1, 1000, 1)
        barFeed.addTrade(datetime.datetime(2000, 1, 2), 1, 1000, 0.01)
        barFeed.addTrade(datetime.datetime(2000, 1, 3), 1, 1000, 0.00441376)
        barFeed.addTrade(datetime.datetime(2000, 1, 4), 1, 1000, 0.00445547)
        barFeed.addTrade(datetime.datetime(2000, 1, 5), 1, 1000, 0.00113077)

        brk = broker.PaperTradingBroker(1000, barFeed)
        strat = Strategy(barFeed, brk)
        strat.run()

        self.assertEquals(brk.getShares("BTC"), 0)
        self.assertEquals(strat.pos.getEntryOrder().getAvgFillPrice(), 1000)
        self.assertEquals(strat.pos.getExitOrder().getAvgFillPrice(), 1000)
        self.assertEquals(strat.pos.getEntryOrder().getFilled(), 0.01)
        self.assertEquals(strat.pos.getExitOrder().getFilled(), 0.01)
        self.assertEquals(strat.pos.getEntryOrder().getRemaining(), 0)
        self.assertEquals(strat.pos.getExitOrder().getRemaining(), 0)
        self.assertEquals(strat.pos.getEntryOrder().getSubmitDateTime().date(), wsclient.get_current_datetime().date())
        self.assertEquals(strat.pos.getExitOrder().getSubmitDateTime().date(), wsclient.get_current_datetime().date())

        self.assertFalse(strat.pos.isOpen())
        self.assertEquals(len(strat.posExecutionInfo), 2)
        self.assertEquals(strat.pos.getShares(), 0.0)

    def testInvalidOrders(self):
        barFeed = TestingLiveTradeFeed()
        brk = broker.PaperTradingBroker(1000, barFeed)
        with self.assertRaises(Exception):
            brk.createLimitOrder(basebroker.Order.Action.BUY, "none", 1, 1)
        with self.assertRaises(Exception):
            brk.createLimitOrder(basebroker.Order.Action.SELL_SHORT, "none", 1, 1)
        with self.assertRaises(Exception):
            brk.createMarketOrder(basebroker.Order.Action.BUY, "none", 1)
        with self.assertRaises(Exception):
            brk.createStopOrder(basebroker.Order.Action.BUY, "none", 1, 1)
        with self.assertRaises(Exception):
            brk.createStopLimitOrder(basebroker.Order.Action.BUY, "none", 1, 1, 1)

    def testBuyWithoutCash(self):
        class Strategy(TestStrategy):
            def __init__(self, feed, brk):
                TestStrategy.__init__(self, feed, brk)
                self.errors = 0

            def onBars(self, bars):
                try:
                    self.limitOrder("BTC", 10, 1)
                except Exception:
                    self.errors += 1

        barFeed = TestingLiveTradeFeed()
        barFeed.addTrade(datetime.datetime(2000, 1, 1), 1, 100, 0.1)
        barFeed.addTrade(datetime.datetime(2000, 1, 2), 1, 100, 0.1)
        barFeed.addTrade(datetime.datetime(2000, 1, 2), 1, 101, 10)
        barFeed.addTrade(datetime.datetime(2000, 1, 3), 1, 100, 0.2)

        brk = broker.PaperTradingBroker(0, barFeed)
        strat = Strategy(barFeed, brk)
        strat.run()

        self.assertEquals(strat.errors, 4)
        self.assertEquals(brk.getShares("BTC"), 0)
        self.assertEquals(brk.getCash(), 0)

    def testRanOutOfCash(self):
        class Strategy(TestStrategy):
            def __init__(self, feed, brk):
                TestStrategy.__init__(self, feed, brk)
                self.errors = 0

            def onBars(self, bars):
                try:
                    self.limitOrder("BTC", 100, 0.1)
                except Exception:
                    self.errors += 1

        barFeed = TestingLiveTradeFeed()
        barFeed.addTrade(datetime.datetime(2000, 1, 1), 1, 100, 10)
        barFeed.addTrade(datetime.datetime(2000, 1, 2), 1, 100, 10)
        barFeed.addTrade(datetime.datetime(2000, 1, 3), 1, 100, 10)

        brk = broker.PaperTradingBroker(10.025, barFeed)
        strat = Strategy(barFeed, brk)
        strat.run()

        self.assertEquals(strat.errors, 2)
        self.assertEquals(brk.getShares("BTC"), 0.1)
        self.assertEquals(brk.getCash(), 0)

    def testSellWithoutBTC(self):
        class Strategy(TestStrategy):
            def __init__(self, feed, brk):
                TestStrategy.__init__(self, feed, brk)
                self.errors = 0

            def onBars(self, bars):
                try:
                    self.limitOrder("BTC", 100, -0.1)
                except Exception:
                    self.errors += 1

        barFeed = TestingLiveTradeFeed()
        barFeed.addTrade(datetime.datetime(2000, 1, 1), 1, 100, 10)
        barFeed.addTrade(datetime.datetime(2000, 1, 2), 1, 100, 10)

        brk = broker.PaperTradingBroker(0, barFeed)
        strat = Strategy(barFeed, brk)
        strat.run()

        self.assertEquals(strat.errors, 2)
        self.assertEquals(brk.getShares("BTC"), 0)
        self.assertEquals(brk.getCash(), 0)

    def testRanOutOfCoins(self):
        class Strategy(TestStrategy):
            def __init__(self, feed, brk):
                TestStrategy.__init__(self, feed, brk)
                self.errors = 0
                self.bought = False

            def onBars(self, bars):
                if not self.bought:
                    self.limitOrder("BTC", 100, 0.1)
                    self.bought = True
                else:
                    try:
                        self.limitOrder("BTC", 100, -0.1)
                    except Exception:
                        self.errors += 1

        barFeed = TestingLiveTradeFeed()
        barFeed.addTrade(datetime.datetime(2000, 1, 1), 1, 100, 10)
        barFeed.addTrade(datetime.datetime(2000, 1, 2), 1, 100, 10)
        barFeed.addTrade(datetime.datetime(2000, 1, 3), 1, 100, 10)

        brk = broker.PaperTradingBroker(10.05, barFeed)
        strat = Strategy(barFeed, brk)
        strat.run()

        self.assertEquals(strat.errors, 1)
        self.assertEquals(brk.getShares("BTC"), 0)
        self.assertEquals(brk.getCash(), 10)


class LiveTradingTestCase(tc_common.TestCase):
    def testMapUserTransactionsToOrderEvents(self):
        class Strategy(TestStrategy):
            def __init__(self, feed, brk):
                TestStrategy.__init__(self, feed, brk)

            def onBars(self, bars):
                self.stop()

        barFeed = TestingLiveTradeFeed()
        # This is to hit onBars and stop strategy execution.
        barFeed.addTrade(datetime.datetime.now(), 1, 100, 1)

        brk = TestingLiveBroker(None, None, None)
        httpClient = brk.getHTTPClient()
        httpClient.setUSDAvailable(0)
        httpClient.setBTCAvailable(0.1)

        httpClient.addOpenOrder(1, -0.1, 578.79)
        httpClient.addOpenOrder(2, 0.1, 567.21)

        httpClient.addUserTransaction(1, -0.04557395, 26.38, 578.79, 0.14)
        httpClient.addUserTransaction(2, 0.04601436, -26.10, 567.21, 0.14)

        strat = Strategy(barFeed, brk)
        strat.run()

        self.assertEquals(len(strat.orderExecutionInfo), 2)
        self.assertEquals(strat.orderExecutionInfo[0].getPrice(), 578.79)
        self.assertEquals(strat.orderExecutionInfo[0].getQuantity(), 0.04557395)
        self.assertEquals(strat.orderExecutionInfo[0].getCommission(), 0.14)
        self.assertEquals(strat.orderExecutionInfo[0].getDateTime().date(), datetime.datetime.now().date())
        self.assertEquals(strat.orderExecutionInfo[1].getPrice(), 567.21)
        self.assertEquals(strat.orderExecutionInfo[1].getQuantity(), 0.04601436)
        self.assertEquals(strat.orderExecutionInfo[1].getCommission(), 0.14)
        self.assertEquals(strat.orderExecutionInfo[1].getDateTime().date(), datetime.datetime.now().date())

    def testCancelOrder(self):
        class Strategy(TestStrategy):
            def __init__(self, feed, brk):
                TestStrategy.__init__(self, feed, brk)

            def onBars(self, bars):
                order = self.getBroker().getActiveOrders()[0]
                self.getBroker().cancelOrder(order)
                self.stop()

        barFeed = TestingLiveTradeFeed()
        # This is to hit onBars and stop strategy execution.
        barFeed.addTrade(datetime.datetime.now(), 1, 100, 1)

        brk = TestingLiveBroker(None, None, None)
        httpClient = brk.getHTTPClient()
        httpClient.setUSDAvailable(0)
        httpClient.setBTCAvailable(0)
        httpClient.addOpenOrder(1, 0.1, 578.79)

        strat = Strategy(barFeed, brk)
        strat.run()

        self.assertEquals(brk.getShares("BTC"), 0)
        self.assertEquals(brk.getCash(), 0)
        self.assertEquals(len(strat.orderExecutionInfo), 1)
        self.assertEquals(strat.orderExecutionInfo[0], None)
        self.assertEquals(len(strat.ordersUpdated), 1)
        self.assertTrue(strat.ordersUpdated[0].isCanceled())

    def testBuyAndSell(self):
        class Strategy(TestStrategy):
            def __init__(self, feed, brk):
                TestStrategy.__init__(self, feed, brk)
                self.buyOrder = None
                self.sellOrder = None

            def onOrderUpdated(self, order):
                TestStrategy.onOrderUpdated(self, order)

                if order == self.buyOrder and order.isPartiallyFilled():
                    if self.sellOrder is None:
                        self.sellOrder = self.limitOrder(common.btc_symbol, 10, -0.5)
                        brk.getHTTPClient().addUserTransaction(self.sellOrder.getId(), -0.5, 5, 10, 0.01)
                elif order == self.sellOrder and order.isFilled():
                    self.stop()

            def onBars(self, bars):
                if self.buyOrder is None:
                    self.buyOrder = self.limitOrder(common.btc_symbol, 10, 1)
                    brk.getHTTPClient().addUserTransaction(self.buyOrder.getId(), 0.5, -5, 10, 0.01)

        barFeed = TestingLiveTradeFeed()
        # This is to get onBars called once.
        barFeed.addTrade(datetime.datetime.now(), 1, 100, 1)

        brk = TestingLiveBroker(None, None, None)
        httpClient = brk.getHTTPClient()
        httpClient.setUSDAvailable(10)
        httpClient.setBTCAvailable(0)

        strat = Strategy(barFeed, brk)
        strat.run()

        self.assertTrue(strat.buyOrder.isPartiallyFilled())
        self.assertTrue(strat.sellOrder.isFilled())
        # 2 events for each order: 1 for accepted, 1 for fill.
        self.assertEquals(len(strat.orderExecutionInfo), 4)
        self.assertEquals(strat.orderExecutionInfo[0], None)
        self.assertEquals(strat.orderExecutionInfo[1].getPrice(), 10)
        self.assertEquals(strat.orderExecutionInfo[1].getQuantity(), 0.5)
        self.assertEquals(strat.orderExecutionInfo[1].getCommission(), 0.01)
        self.assertEquals(strat.orderExecutionInfo[1].getDateTime().date(), datetime.datetime.now().date())
        self.assertEquals(strat.orderExecutionInfo[2], None)
        self.assertEquals(strat.orderExecutionInfo[3].getPrice(), 10)
        self.assertEquals(strat.orderExecutionInfo[3].getQuantity(), 0.5)
        self.assertEquals(strat.orderExecutionInfo[3].getCommission(), 0.01)
        self.assertEquals(strat.orderExecutionInfo[3].getDateTime().date(), datetime.datetime.now().date())


class WebSocketTestCase(tc_common.TestCase):
    def testBarFeed(self):
        events = {
            "on_bars": False,
            "on_order_book_updated": False,
            "break": False,
            "start": datetime.datetime.now()
        }

        disp = dispatcher.Dispatcher()
        barFeed = barfeed.LiveTradeFeed()
        disp.addSubject(barFeed)

        def on_bars(dateTime, bars):
            bars[common.btc_symbol]
            events["on_bars"] = True
            if events["on_order_book_updated"] is True:
                disp.stop()

        def on_order_book_updated(orderBookUpdate):
            events["on_order_book_updated"] = True
            if events["on_bars"] is True:
                disp.stop()

        def on_idle():
            # Stop after 5 minutes.
            if (datetime.datetime.now() - events["start"]).seconds > 60*5:
                disp.stop()

        # Subscribe to events.
        barFeed.getNewValuesEvent().subscribe(on_bars)
        barFeed.getOrderBookUpdateEvent().subscribe(on_order_book_updated)
        disp.getIdleEvent().subscribe(on_idle)
        disp.run()

        # Check that we received both events.
        self.assertTrue(events["on_bars"])
        self.assertTrue(events["on_order_book_updated"])
