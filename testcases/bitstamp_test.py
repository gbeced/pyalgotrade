# PyAlgoTrade
#
# Copyright 2011-2014 Gabriel Martin Becedillas Ruiz
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

import unittest
import datetime
import time
import threading
import Queue
import json

from pyalgotrade import broker as basebroker
from pyalgotrade.bitstamp import barfeed
from pyalgotrade.bitstamp import broker
from pyalgotrade.bitstamp import wsclient
from pyalgotrade.bitstamp import common
from pyalgotrade import strategy


class TestingWebSocketClientThread(threading.Thread):
    def __init__(self, events):
        threading.Thread.__init__(self)
        self.__queue = Queue.Queue()
        self.__queue.put((wsclient.WebSocketClient.ON_CONNECTED, None))
        for event in events:
            self.__queue.put(event)
        self.__queue.put((wsclient.WebSocketClient.ON_DISCONNECTED, None))

    def getQueue(self):
        return self.__queue

    def start(self):
        threading.Thread.start(self)

    def run(self):
        while not self.__queue.empty():
            time.sleep(0.01)

    def stop(self):
        pass


class TestingLiveTradeFeed(barfeed.LiveTradeFeed):
    def __init__(self):
        barfeed.LiveTradeFeed.__init__(self)
        self.__events = []

    def addTrade(self, dateTime, tid, price, amount):
        dataDict = {
            "id": tid,
            "price": price,
            "amount": amount
            }
        eventDict = {}
        eventDict["data"] = json.dumps(dataDict)
        self.__events.append((wsclient.WebSocketClient.ON_TRADE, wsclient.Trade(dateTime, eventDict)))

    def buildWebSocketClientThread(self):
        return TestingWebSocketClientThread(self.__events)


class TestStrategy(strategy.BaseStrategy):
    def __init__(self, feed, brk):
        strategy.BaseStrategy.__init__(self, feed, brk)
        self.bid = None
        self.ask = None
        self.posExecutionInfo = []

        # Subscribe to order book update events to get bid/ask prices to trade.
        feed.getOrderBookUpdateEvent().subscribe(self.__onOrderBookUpdate)

    def __onOrderBookUpdate(self, orderBookUpdate):
        bid = orderBookUpdate.getBidPrices()[0]
        ask = orderBookUpdate.getAskPrices()[0]

        if bid != self.bid or ask != self.ask:
            self.bid = bid
            self.ask = ask

    def onEnterOk(self, position):
        self.posExecutionInfo.append(position.getEntryOrder().getExecutionInfo())

    def onEnterCanceled(self, position):
        self.posExecutionInfo.append(position.getEntryOrder().getExecutionInfo())

    def onExitOk(self, position):
        self.posExecutionInfo.append(position.getExitOrder().getExecutionInfo())

    def onExitCanceled(self, position):
        self.posExecutionInfo.append(position.getExitOrder().getExecutionInfo())


class InstrumentTraitsTestCase(unittest.TestCase):
    def testInstrumentTraits(self):
        traits = common.BTCTraits()
        self.assertEqual(traits.roundQuantity(0), 0)
        self.assertEqual(traits.roundQuantity(1), 1)
        self.assertEqual(traits.roundQuantity(1.1 + 1.1 + 1.1), 3.3)
        self.assertEqual(traits.roundQuantity(1.1 + 1.1 + 1.1 - 3.3), 0)
        self.assertEqual(traits.roundQuantity(0.00441376), 0.00441376)
        self.assertEqual(traits.roundQuantity(0.004413764), 0.00441376)


class PaperTradingTestCase(unittest.TestCase):
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
        self.assertEqual(round(strat.pos.getShares(), 3), 0.3)
        self.assertEqual(len(strat.posExecutionInfo), 1)
        self.assertEqual(strat.pos.getEntryOrder().getSubmitDateTime().date(), wsclient.get_current_datetime().date())

    def testBuyAndSellWithPartialFill1(self):

        class Strategy(TestStrategy):
            def __init__(self, feed, brk):
                TestStrategy.__init__(self, feed, brk)
                self.pos = None

            def onBars(self, bars):
                if self.pos is None:
                    self.pos = self.enterLongLimit("BTC", 100, 1, True)
                elif bars.getDateTime() == datetime.datetime(2000, 1, 3):
                    self.pos.exit(limitPrice=101)

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
        self.assertEqual(round(strat.pos.getShares(), 3), 0.1)
        self.assertEqual(len(strat.posExecutionInfo), 1)
        self.assertEqual(strat.pos.getEntryOrder().getSubmitDateTime().date(), wsclient.get_current_datetime().date())
        self.assertEqual(strat.pos.getExitOrder().getSubmitDateTime().date(), wsclient.get_current_datetime().date())

    def testBuyAndSellWithPartialFill2(self):

        class Strategy(TestStrategy):
            def __init__(self, feed, brk):
                TestStrategy.__init__(self, feed, brk)
                self.pos = None

            def onBars(self, bars):
                if self.pos is None:
                    self.pos = self.enterLongLimit("BTC", 100, 1, True)
                elif bars.getDateTime() == datetime.datetime(2000, 1, 3):
                    self.pos.exit(limitPrice=101)

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
        self.assertEqual(strat.pos.getShares(), 0)
        self.assertEqual(len(strat.posExecutionInfo), 2)
        self.assertEqual(strat.pos.getEntryOrder().getSubmitDateTime().date(), wsclient.get_current_datetime().date())
        self.assertEqual(strat.pos.getExitOrder().getSubmitDateTime().date(), wsclient.get_current_datetime().date())

    def testRoundingBugWithTrades(self):
        # Unless proper rounding is in place 0.01 - 0.00441376 - 0.00445547 - 0.00113077 == 6.50521303491e-19
        # instead of 0.

        class Strategy(TestStrategy):
            def __init__(self, feed, brk):
                TestStrategy.__init__(self, feed, brk)
                self.pos = None

            def onBars(self, bars):
                if self.pos is None:
                    self.pos = self.enterLongLimit("BTC", 100, 0.01, True)
                elif self.pos.entryFilled() and not self.pos.getExitOrder():
                    self.pos.exitLimit(100, True)

        barFeed = TestingLiveTradeFeed()
        barFeed.addTrade(datetime.datetime(2000, 1, 1), 1, 100, 1)
        barFeed.addTrade(datetime.datetime(2000, 1, 2), 1, 100, 0.01)
        barFeed.addTrade(datetime.datetime(2000, 1, 3), 1, 100, 0.00441376)
        barFeed.addTrade(datetime.datetime(2000, 1, 4), 1, 100, 0.00445547)
        barFeed.addTrade(datetime.datetime(2000, 1, 5), 1, 100, 0.00113077)

        brk = broker.PaperTradingBroker(1000, barFeed)
        strat = Strategy(barFeed, brk)
        strat.run()

        self.assertEqual(brk.getShares("BTC"), 0)
        self.assertEqual(strat.pos.getEntryOrder().getAvgFillPrice(), 100)
        self.assertEqual(strat.pos.getExitOrder().getAvgFillPrice(), 100)
        self.assertEqual(strat.pos.getEntryOrder().getFilled(), 0.01)
        self.assertEqual(strat.pos.getExitOrder().getFilled(), 0.01)
        self.assertEqual(strat.pos.getEntryOrder().getRemaining(), 0)
        self.assertEqual(strat.pos.getExitOrder().getRemaining(), 0)
        self.assertEqual(strat.pos.getEntryOrder().getSubmitDateTime().date(), wsclient.get_current_datetime().date())
        self.assertEqual(strat.pos.getExitOrder().getSubmitDateTime().date(), wsclient.get_current_datetime().date())

        self.assertFalse(strat.pos.isOpen())
        self.assertEqual(len(strat.posExecutionInfo), 2)
        self.assertEqual(strat.pos.getShares(), 0.0)

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
