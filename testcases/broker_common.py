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
.. module:: broker_common
   :synopsis: Test cases and utilities that can be reused across different broker implementations.
.. moduleauthor:: Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>
"""

import unittest
import datetime

from pyalgotrade import broker
from pyalgotrade import bar
from pyalgotrade import barfeed

class Callback:
    def __init__(self):
        self.eventCount = 0

    def onOrderUpdated(self, broker_, order):
        self.eventCount += 1

class BarsBuilder(object):
    def __init__(self, instrument, frequency):
        self.__instrument = instrument
        self.__frequency = frequency
        self.__nextDateTime = datetime.datetime(2011, 1, 1)
        if frequency == bar.Frequency.TRADE:
            self.__delta = datetime.timedelta(milliseconds=1)
        elif frequency == bar.Frequency.SECOND:
            self.__delta = datetime.timedelta(seconds=1)
        elif frequency == bar.Frequency.MINUTE:
            self.__delta = datetime.timedelta(minutes=1)
        elif frequency == bar.Frequency.HOUR:
            self.__delta = datetime.timedelta(hours=1)
        elif frequency == bar.Frequency.DAY:
            self.__delta = datetime.timedelta(days=1)
        else:
            raise Exception("Invalid frequency")

    def advance(self, sessionClose):
        if sessionClose:
            self.__nextDateTime = datetime.datetime(self.__nextDateTime.year, self.__nextDateTime.month, self.__nextDateTime.day)
            self.__nextDateTime += datetime.timedelta(days=1)
        else:
            self.__nextDateTime += self.__delta

    def nextBars(self, openPrice, highPrice, lowPrice, closePrice, volume=None, sessionClose=False):
        if volume is None:
            volume = closePrice*10
        bar_ = bar.BasicBar(self.__nextDateTime, openPrice, highPrice, lowPrice, closePrice, volume, closePrice, self.__frequency)
        bar_.setSessionClose(sessionClose)
        ret = {self.__instrument : bar_}
        self.advance(sessionClose)
        return bar.Bars(ret)

    def nextTuple(self, openPrice, highPrice, lowPrice, closePrice, volume=None, sessionClose=False):
        ret = self.nextBars(openPrice, highPrice, lowPrice, closePrice, volume, sessionClose)
        return (ret.getDateTime(), ret)

class BrokerFactory():
    def getBroker(self, cash, barFeed, commission=None):
        raise NotImplementedError()

    def getFixedCommissionPerTrade(self, amount):
        raise NotImplementedError()

class BrokerVisitor():
    def onBars(self, broker, dateTime, bars):
        raise NotImplementedError()

class BaseTestCase(unittest.TestCase):
    TestInstrument = "orcl"
    Factory = BrokerFactory()
    Visitor = BrokerVisitor()

class BrokerTestCase(BaseTestCase):
    def testRegressionGetActiveOrders(self):
        activeOrders = []

        def onOrderUpdated(broker, order):
            activeOrders.append(len(broker.getActiveOrders()))

        brk = self.Factory.getBroker(1000, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        brk.getOrderUpdatedEvent().subscribe(onOrderUpdated)
        o1 = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
        brk.placeOrder(o1)
        o2 = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
        brk.placeOrder(o2)

        self.assertEqual(o1.getFilled(), 0)
        self.assertEqual(o2.getFilled(), 0)
        self.assertEqual(o1.getRemaining(), o1.getQuantity())
        self.assertEqual(o2.getRemaining(), o2.getQuantity())

        self.Visitor.onBars(brk, *barsBuilder.nextTuple(10, 15, 8, 12))

        self.assertEqual(o1.getFilled(), 1)
        self.assertEqual(o2.getFilled(), 1)
        self.assertEqual(o1.getRemaining(), 0)
        self.assertEqual(o2.getRemaining(), 0)
        self.assertEqual(brk.getCash(), 1000 - 10*2)
        self.assertEqual(len(activeOrders), 4)
        self.assertEqual(activeOrders[0], 2)  # First order gets accepted, both orders are active.
        self.assertEqual(activeOrders[1], 1)  # First order gets filled, one order is active.
        self.assertEqual(activeOrders[2], 1)  # Second order gets accepted, one order is active.
        self.assertEqual(activeOrders[3], 0)  # Second order gets filled, zero orders are active.

class MarketOrderTestCase(BaseTestCase):
    def testBuyAndSell(self):
        brk = self.Factory.getBroker(11, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Buy
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(10, 15, 8, 12))
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getPrice(), 10)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        self.assertEqual(len(brk.getActiveOrders()), 0)
        self.assertEqual(brk.getCash(), 1)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 1)
        self.assertEqual(cb.eventCount, 2)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

        # Sell
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        order = brk.createMarketOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.placeOrder(order)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(10, 15, 8, 12))
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getPrice(), 10)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        self.assertEqual(len(brk.getActiveOrders()), 0)
        self.assertEqual(brk.getCash(), 11)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 0)
        self.assertEqual(cb.eventCount, 2)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

    def testFailToBuy(self):
        brk = self.Factory.getBroker(5, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)

        # Fail to buy. No money.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(10, 15, 8, 12))
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getExecutionInfo(), None)
        self.assertEqual(len(brk.getActiveOrders()), 1)
        self.assertEqual(brk.getCash(), 5)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 0)
        self.assertEqual(cb.eventCount, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Fail to buy. No money. Canceled due to session close.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(11, 15, 8, 12, sessionClose=True))
        self.assertTrue(order.isCanceled())
        self.assertEqual(order.getExecutionInfo(), None)
        self.assertEqual(len(brk.getActiveOrders()), 0)
        self.assertEqual(brk.getCash(), 5)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 0)
        self.assertEqual(cb.eventCount, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

    def testBuy_GTC(self):
        brk = self.Factory.getBroker(5, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
        order.setGoodTillCanceled(True)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Fail to buy. No money.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        brk.placeOrder(order)
        # Set sessionClose to true test that the order doesn't get canceled.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(10, 15, 8, 12, sessionClose=True))
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getExecutionInfo(), None)
        self.assertEqual(len(brk.getActiveOrders()), 1)
        self.assertEqual(brk.getCash(), 5)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 0)
        self.assertEqual(cb.eventCount, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Buy
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(2, 15, 1, 12))
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getPrice(), 2)
        self.assertEqual(len(brk.getActiveOrders()), 0)
        self.assertEqual(brk.getCash(), 3)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 1)
        self.assertEqual(cb.eventCount, 1)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

    def testBuyAndSellInTwoSteps(self):
        brk = self.Factory.getBroker(20.4, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Buy
        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 2)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 2)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(10, 15, 8, 12))
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getPrice(), 10)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        self.assertEqual(len(brk.getActiveOrders()), 0)
        self.assertEqual(round(brk.getCash(), 1),  0.4)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 2)
        self.assertEqual(order.getFilled(), 2)
        self.assertEqual(order.getRemaining(), 0)

        # Sell
        order = brk.createMarketOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(10, 15, 8, 12))
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getPrice(), 10)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        self.assertEqual(len(brk.getActiveOrders()), 0)
        self.assertEqual(round(brk.getCash(), 1),  10.4)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 1)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

        # Sell again
        order = brk.createMarketOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.placeOrder(order)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(11, 15, 8, 12))
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getPrice(), 11)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        self.assertEqual(len(brk.getActiveOrders()), 0)
        self.assertEqual(round(brk.getCash(), 1),  21.4)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 0)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

    def testBuyWithCommission(self):
        brk = self.Factory.getBroker(1020, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE),
                                     commission=self.Factory.getFixedCommissionPerTrade(10))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Buy
        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 100)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 100)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(10, 15, 8, 12, volume=500))
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getCommission(), 10)
        self.assertEqual(len(brk.getActiveOrders()), 0)
        self.assertEqual(brk.getCash(), 10)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 100)
        self.assertEqual(order.getFilled(), 100)
        self.assertEqual(order.getRemaining(), 0)

    def testSellShort_3(self):
        brk = self.Factory.getBroker(100, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Buy 1
        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.placeOrder(order)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(100, 100, 100, 100))
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 1)
        self.assertEqual(brk.getCash(), 0)

        # Sell 2
        order = brk.createMarketOrder(broker.Order.Action.SELL_SHORT, BaseTestCase.TestInstrument, 2)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 2)
        brk.placeOrder(order)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(100, 100, 100, 100))
        self.assertEqual(order.getFilled(), 2)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), -1)
        self.assertEqual(brk.getCash(), 200)

        # Buy 1
        order = brk.createMarketOrder(broker.Order.Action.BUY_TO_COVER, BaseTestCase.TestInstrument, 1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(100, 100, 100, 100))
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 0)
        self.assertEqual(brk.getCash(), 100)

    def testSellShortWithCommission(self):
        sharePrice = 100
        commission = 10
        brk = self.Factory.getBroker(1010, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE),
                                     commission=self.Factory.getFixedCommissionPerTrade(commission))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Sell 10 shares
        order = brk.createMarketOrder(broker.Order.Action.SELL_SHORT, BaseTestCase.TestInstrument, 10)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 10)
        brk.placeOrder(order)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(sharePrice, sharePrice, sharePrice, sharePrice))
        self.assertEqual(order.getFilled(), 10)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getCommission(), 10)
        self.assertEqual(brk.getCash(), 2000)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), -10)

        # Buy the 10 shares sold short plus 9 extra
        order = brk.createMarketOrder(broker.Order.Action.BUY_TO_COVER, BaseTestCase.TestInstrument, 19)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 19)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(sharePrice, sharePrice, sharePrice, sharePrice))
        self.assertEqual(order.getFilled(), 19)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getCommission(), 10)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 9)
        self.assertEqual(brk.getCash(), sharePrice - commission)

    def testCancel(self):
        brk = self.Factory.getBroker(100, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.cancelOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(10, 10, 10, 10))
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.assertTrue(order.isCanceled())


class LimitOrderTestCase(BaseTestCase):
    def testBuyAndSell_HitTargetPrice(self):
        brk = self.Factory.getBroker(20, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Buy
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        order = brk.createLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 10, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.placeOrder(order)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(12, 15, 8, 12))
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getPrice(), 10)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        self.assertEqual(len(brk.getActiveOrders()), 0)
        self.assertEqual(brk.getCash(), 10)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 1)
        self.assertEqual(cb.eventCount, 2)

        # Sell
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        order = brk.createLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 15, 1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(10, 17, 8, 10))
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getPrice(), 15)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        self.assertEqual(len(brk.getActiveOrders()), 0)
        self.assertEqual(brk.getCash(), 25)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 0)
        self.assertEqual(cb.eventCount, 2)

    def testBuyAndSell_GetBetterPrice(self):
        brk = self.Factory.getBroker(20, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Buy
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        order = brk.createLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 14, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.placeOrder(order)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(12, 15, 8, 12))
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getPrice(), 12)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        self.assertEqual(len(brk.getActiveOrders()), 0)
        self.assertEqual(brk.getCash(), 8)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 1)
        self.assertEqual(cb.eventCount, 2)

        # Sell
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        order = brk.createLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 15, 1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(16, 17, 8, 10))
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getPrice(), 16)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        self.assertEqual(len(brk.getActiveOrders()), 0)
        self.assertEqual(brk.getCash(), 24)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 0)
        self.assertEqual(cb.eventCount, 2)

    def testBuyAndSell_GappingBars(self):
        brk = self.Factory.getBroker(20, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Buy. Bar is below the target price.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        order = brk.createLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 20, 1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(10, 15, 8, 10))
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getPrice(), 10)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        self.assertEqual(len(brk.getActiveOrders()), 0)
        self.assertEqual(brk.getCash(), 10)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 1)
        self.assertEqual(cb.eventCount, 2)

        # Sell. Bar is above the target price.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        order = brk.createLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 30, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.placeOrder(order)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(35, 40, 32, 35))
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getPrice(), 35)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        self.assertEqual(len(brk.getActiveOrders()), 0)
        self.assertEqual(brk.getCash(), 45)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 0)
        self.assertEqual(cb.eventCount, 2)

    def testFailToBuy(self):
        brk = self.Factory.getBroker(5, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        order = brk.createLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 5, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Fail to buy (couldn't get specific price).
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        brk.placeOrder(order)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(10, 15, 8, 12))
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getExecutionInfo(), None)
        self.assertEqual(len(brk.getActiveOrders()), 1)
        self.assertEqual(brk.getCash(), 5)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 0)
        self.assertEqual(cb.eventCount, 1)

        # Fail to buy (couldn't get specific price). Canceled due to session close.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(11, 15, 8, 12, sessionClose=True))
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.assertTrue(order.isCanceled())
        self.assertEqual(order.getExecutionInfo(), None)
        self.assertEqual(len(brk.getActiveOrders()), 0)
        self.assertEqual(brk.getCash(), 5)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 0)
        self.assertEqual(cb.eventCount, 1)

    def testBuy_GTC(self):
        brk = self.Factory.getBroker(10, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        order = brk.createLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 4, 2)
        order.setGoodTillCanceled(True)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 2)

        # Fail to buy (couldn't get specific price).
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        brk.placeOrder(order)
        # Set sessionClose to true test that the order doesn't get canceled.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(10, 15, 8, 12, sessionClose=True))
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 2)
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getExecutionInfo(), None)
        self.assertEqual(len(brk.getActiveOrders()), 1)
        self.assertEqual(brk.getCash(), 10)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 0)
        self.assertEqual(cb.eventCount, 1)

        # Buy
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(2, 15, 1, 12))
        self.assertEqual(order.getFilled(), 2)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getPrice(), 2)
        self.assertEqual(len(brk.getActiveOrders()), 0)
        self.assertEqual(brk.getCash(), 6)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 2)
        self.assertEqual(cb.eventCount, 1)


class StopOrderTestCase(BaseTestCase):
    def testLongPosStopLoss(self):
        brk = self.Factory.getBroker(15, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Buy
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.placeOrder(order)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(10, 15, 8, 12))
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getExecutionInfo().getPrice(), 10)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        self.assertEqual(len(brk.getActiveOrders()), 0)
        self.assertEqual(brk.getCash(), 5)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 1)
        self.assertEqual(cb.eventCount, 2)

        # Create stop loss order.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        order = brk.createStopOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 9, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.placeOrder(order)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(10, 15, 10, 12))  # Stop loss not hit.
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.assertFalse(order.isFilled())
        self.assertEqual(len(brk.getActiveOrders()), 1)
        self.assertEqual(brk.getCash(), 5)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 1)
        self.assertEqual(cb.eventCount, 1)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(10, 15, 8, 12))  # Stop loss hit.
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getPrice(), 9)
        self.assertEqual(len(brk.getActiveOrders()), 0)
        self.assertEqual(brk.getCash(), 5+9)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 0)
        self.assertEqual(cb.eventCount, 2)

    def testLongPosStopLoss_GappingBars(self):
        brk = self.Factory.getBroker(15, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Buy
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.placeOrder(order)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(10, 15, 8, 12))
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getExecutionInfo().getPrice(), 10)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        self.assertEqual(len(brk.getActiveOrders()), 0)
        self.assertEqual(brk.getCash(), 5)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 1)
        self.assertEqual(cb.eventCount, 2)

        # Create stop loss order.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        order = brk.createStopOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 9, 1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(10, 15, 10, 12))  # Stop loss not hit.
        self.assertFalse(order.isFilled())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.assertEqual(len(brk.getActiveOrders()), 1)
        self.assertEqual(brk.getCash(), 5)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 1)
        self.assertEqual(cb.eventCount, 1)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(5, 8, 4, 7))  # Stop loss hit.
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getExecutionInfo().getPrice(), 5)
        self.assertEqual(len(brk.getActiveOrders()), 0)
        self.assertEqual(brk.getCash(), 5+5)  # Fill the stop loss order at open price.
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 0)
        self.assertEqual(cb.eventCount, 2)

    def testShortPosStopLoss(self):
        brk = self.Factory.getBroker(15, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Sell short
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        order = brk.createMarketOrder(broker.Order.Action.SELL_SHORT, BaseTestCase.TestInstrument, 1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(10, 15, 8, 12))
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getExecutionInfo().getPrice(), 10)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        self.assertEqual(len(brk.getActiveOrders()), 0)
        self.assertEqual(brk.getCash(), 15+10)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), -1)
        self.assertEqual(cb.eventCount, 2)

        # Create stop loss order.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        order = brk.createStopOrder(broker.Order.Action.BUY_TO_COVER, BaseTestCase.TestInstrument, 11, 1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(8, 10, 7, 9))  # Stop loss not hit.
        self.assertFalse(order.isFilled())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.assertEqual(len(brk.getActiveOrders()), 1)
        self.assertEqual(brk.getCash(), 15+10)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), -1)
        self.assertEqual(cb.eventCount, 1)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(10, 15, 8, 12))  # Stop loss hit.
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getExecutionInfo().getPrice(), 11)
        self.assertEqual(len(brk.getActiveOrders()), 0)
        self.assertEqual(brk.getCash(), 15-1)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 0)
        self.assertEqual(cb.eventCount, 2)

    def testShortPosStopLoss_GappingBars(self):
        brk = self.Factory.getBroker(15, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Sell short
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        order = brk.createMarketOrder(broker.Order.Action.SELL_SHORT, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.placeOrder(order)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(10, 15, 8, 12))
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getExecutionInfo().getPrice(), 10)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        self.assertEqual(len(brk.getActiveOrders()), 0)
        self.assertEqual(brk.getCash(), 15+10)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), -1)
        self.assertEqual(cb.eventCount, 2)

        # Create stop loss order.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        order = brk.createStopOrder(broker.Order.Action.BUY_TO_COVER, BaseTestCase.TestInstrument, 11, 1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(8, 10, 7, 9))  # Stop loss not hit.
        self.assertFalse(order.isFilled())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.assertEqual(len(brk.getActiveOrders()), 1)
        self.assertEqual(brk.getCash(), 15+10)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), -1)
        self.assertEqual(cb.eventCount, 1)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(15, 20, 13, 14))  # Stop loss hit.
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getExecutionInfo().getPrice(), 15)
        self.assertEqual(len(brk.getActiveOrders()), 0)
        self.assertEqual(brk.getCash(), 15-5)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 0)
        self.assertEqual(cb.eventCount, 2)


class StopLimitOrderTestCase(BaseTestCase):
    def testFillOpen(self):
        brk = self.Factory.getBroker(15, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Buy. Stop >= 10. Buy <= 12.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, stopPrice=10, limitPrice=12, quantity=1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price not hit. Limit price not hit.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(8, 9, 7, 8))
        self.assertFalse(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price not hit.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(13, 15, 13, 14))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Limit price hit (bars include the price). Fill at open price.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(11, 15, 10, 14))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getPrice(), 11)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

        # Sell. Stop <= 8. Sell >= 6.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        order = brk.createStopLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, stopPrice=8, limitPrice=6, quantity=1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price not hit. Limit price not hit.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(9, 10, 9, 10))
        self.assertFalse(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price not hit.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(4, 5, 3, 4))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Limit price hit (bars include the price). Fill at open price.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(7, 8, 6, 7))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getPrice(), 7)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

    def testFillOpen_GappingBars(self):
        brk = self.Factory.getBroker(15, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Buy. Stop >= 10. Buy <= 12.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, stopPrice=10, limitPrice=12, quantity=1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price not hit. Limit price not hit.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(8, 9, 7, 8))
        self.assertFalse(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price not hit.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(13, 18, 13, 17))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Limit price hit (bars don't include the price). Fill at open price.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(7, 9, 6, 8))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getPrice(), 7)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

        # Sell. Stop <= 8. Sell >= 6.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        order = brk.createStopLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, stopPrice=8, limitPrice=6, quantity=1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price not hit. Limit price not hit.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(9, 10, 9, 10))
        self.assertFalse(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price not hit.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(4, 5, 3, 4))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Limit price hit (bars don't include the price). Fill at open price.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(10, 12, 8, 10))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getPrice(), 10)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

    def testFillLimit(self):
        brk = self.Factory.getBroker(15, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Buy. Stop >= 10. Buy <= 12.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, stopPrice=10, limitPrice=12, quantity=1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price not hit. Limit price not hit.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(8, 9, 7, 8))
        self.assertFalse(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price not hit.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(13, 15, 13, 14))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Limit price hit. Fill at limit price.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(13, 15, 10, 14))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getPrice(), 12)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

        # Sell. Stop <= 8. Sell >= 6.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        order = brk.createStopLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, stopPrice=8, limitPrice=6, quantity=1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price not hit. Limit price not hit.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(9, 10, 9, 10))
        self.assertFalse(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price not hit.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(4, 5, 3, 4))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Limit price hit. Fill at limit price.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(5, 7, 5, 6))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getPrice(), 6)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

    def testHitStopAndLimit(self):
        brk = self.Factory.getBroker(15, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Buy. Stop >= 10. Buy <= 12.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, stopPrice=10, limitPrice=12, quantity=1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price hit. Fill at stop price.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(9, 15, 8, 14))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getPrice(), 10)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

        # Sell. Stop <= 8. Sell >= 6.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        order = brk.createStopLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, stopPrice=8, limitPrice=6, quantity=1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price hit. Fill at stop price.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(9, 10, 5, 8))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getPrice(), 8)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

    def testInvertedPrices_FillOpen(self):
        brk = self.Factory.getBroker(15, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Buy. Stop >= 12. Buy <= 10.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, stopPrice=12, limitPrice=10, quantity=1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price not hit. Limit price not hit.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(8, 9, 7, 8))
        self.assertFalse(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price not hit.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(11, 12, 10.5, 11))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Limit price hit. Fill at open price.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(9, 15, 8, 14))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getPrice(), 9)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

        # Sell. Stop <= 6. Sell >= 8.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        order = brk.createStopLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, stopPrice=6, limitPrice=8, quantity=1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price not hit. Limit price not hit.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(9, 10, 9, 10))
        self.assertFalse(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price not hit.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(7, 7, 6, 7))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Limit price hit. Fill at open price.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(9, 10, 8, 9))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getPrice(), 9)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

    def testInvertedPrices_FillOpen_GappingBars(self):
        brk = self.Factory.getBroker(15, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Buy. Stop >= 12. Buy <= 10.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, stopPrice=12, limitPrice=10, quantity=1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price not hit. Limit price not hit.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(8, 9, 7, 8))
        self.assertFalse(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price not hit.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(11, 12, 10.5, 11))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Limit price hit. Fill at open price.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(7, 9, 6, 8))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getPrice(), 7)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

        # Sell. Stop <= 6. Sell >= 8.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        order = brk.createStopLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, stopPrice=6, limitPrice=8, quantity=1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price not hit. Limit price not hit.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(9, 10, 9, 10))
        self.assertFalse(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price not hit.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(7, 7, 6, 7))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Limit price hit. Fill at open price.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(10, 10, 9, 9))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getPrice(), 10)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

    def testInvertedPrices_FillLimit(self):
        brk = self.Factory.getBroker(15, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Buy. Stop >= 12. Buy <= 10.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, stopPrice=12, limitPrice=10, quantity=1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price not hit. Limit price not hit.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(8, 9, 7, 8))
        self.assertFalse(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price not hit.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(11, 12, 10.5, 11))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Limit price hit. Fill at limit price.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(11, 13, 8, 9))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getPrice(), 10)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

        # Sell. Stop <= 6. Sell >= 8.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        order = brk.createStopLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, stopPrice=6, limitPrice=8, quantity=1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price not hit. Limit price not hit.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(9, 10, 9, 10))
        self.assertFalse(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price not hit.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(7, 7, 6, 7))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Limit price hit. Fill at limit price.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(7, 10, 6, 9))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getPrice(), 8)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

    def testInvertedPrices_HitStopAndLimit(self):
        brk = self.Factory.getBroker(15, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Buy. Stop >= 12. Buy <= 10.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, stopPrice=12, limitPrice=10, quantity=1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price hit. Fill at limit price.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(9, 15, 8, 14))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getPrice(), 10)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

        # Sell. Stop <= 6. Sell >= 8.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
        order = brk.createStopLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, stopPrice=6, limitPrice=8, quantity=1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price hit. Fill at limit price.
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(6, 10, 5, 7))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getPrice(), 8)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
