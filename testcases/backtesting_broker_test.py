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

import unittest
import datetime

from pyalgotrade import broker
from pyalgotrade.broker import backtesting
from pyalgotrade import bar
from pyalgotrade import barfeed


class Callback:
    def __init__(self):
        self.eventCount = 0

    def onOrderEvent(self, broker_, orderEvent):
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

    # sessionClose is True if the next bars should start at a different date.
    def nextBars(self, openPrice, highPrice, lowPrice, closePrice, volume=None, sessionClose=False):
        if volume is None:
            volume = closePrice*10
        bar_ = bar.BasicBar(self.__nextDateTime, openPrice, highPrice, lowPrice, closePrice, volume, closePrice, self.__frequency)
        ret = {self.__instrument : bar_}
        self.advance(sessionClose)
        return bar.Bars(ret)

    # sessionClose is True if the next bars should start at a different date.
    def nextTuple(self, openPrice, highPrice, lowPrice, closePrice, volume=None, sessionClose=False):
        ret = self.nextBars(openPrice, highPrice, lowPrice, closePrice, volume, sessionClose)
        return (ret.getDateTime(), ret)

class BaseTestCase(unittest.TestCase):
    TestInstrument = "orcl"

class CommissionTestCase(unittest.TestCase):
    def testNoCommission(self):
        comm = backtesting.NoCommission()
        self.assertEqual(comm.calculate(None, 1, 1), 0)

    def testFixedPerTrade(self):
        comm = backtesting.FixedPerTrade(1.2)
        self.assertEqual(comm.calculate(None, 1, 1), 1.2)

    def testTradePercentage(self):
        comm = backtesting.TradePercentage(0.1)
        self.assertEqual(comm.calculate(None, 1, 1), 0.1)
        self.assertEqual(comm.calculate(None, 2, 2), 0.4)


class BrokerTestCase(BaseTestCase):
    def testOneCancelsAnother(self):
        orders = {}

        brk = backtesting.Broker(1000, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        def onOrderEvent(broker_, orderEvent):
            if orderEvent.getEventType() == broker.OrderEvent.Type.FILLED and orderEvent.getOrder().getId() == orders["sell"].getId():
                brk.cancelOrder(orders["stoploss"])

        # Buy order.
        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
        brk.placeOrder(order)
        brk.onBars(*barsBuilder.nextTuple(10, 15, 8, 12))
        self.assertTrue(order.isFilled())

        brk.getOrderUpdatedEvent().subscribe(onOrderEvent)

        # Create a sell limit and a stop loss order.
        order = brk.createLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 11, 1)
        orders["sell"] = order
        brk.placeOrder(order)
        order = brk.createStopOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 8, 1)
        orders["stoploss"] = order
        brk.placeOrder(order)
        brk.onBars(*barsBuilder.nextTuple(10, 15, 5, 12))

        # Only one order (the sell limit order) should have got filled. The other one should be canceled.
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 0)
        self.assertTrue(orders["sell"].isFilled())
        self.assertTrue(orders["stoploss"].isCanceled())

    def testRegressionGetActiveOrders(self):
        activeOrders = []

        def onOrderEvent(broker, orderEvent):
            activeOrders.append(len(broker.getActiveOrders()))

        brk = backtesting.Broker(1000, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        brk.getOrderUpdatedEvent().subscribe(onOrderEvent)
        o1 = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
        brk.placeOrder(o1)
        o2 = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
        brk.placeOrder(o2)

        self.assertEqual(o1.getFilled(), 0)
        self.assertEqual(o2.getFilled(), 0)
        self.assertEqual(o1.getRemaining(), o1.getQuantity())
        self.assertEqual(o2.getRemaining(), o2.getQuantity())

        brk.onBars(*barsBuilder.nextTuple(10, 15, 8, 12))

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

    def testVolumeLimitMinuteBars(self):
        brk = backtesting.Broker(1000, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        orders = []

        # Try with different order types.
        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 3)
        brk.placeOrder(order)
        orders.append(order)
        order = brk.createLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 10, 3)
        brk.placeOrder(order)
        orders.append(order)
        order = brk.createStopOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 10, 3)
        brk.placeOrder(order)
        orders.append(order)
        order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 10, 10, 3)
        brk.placeOrder(order)
        orders.append(order)

        for order in orders:
            self.assertEqual(order.getFilled(), 0)
            self.assertEqual(order.getRemaining(), 3)

        # The orders should not get filled if there is not enough volume.
        brk.onBars(*barsBuilder.nextTuple(10, 15, 8, 12, volume=10))
        for order in orders:
            self.assertFalse(order.isFilled())
            self.assertEqual(order.getFilled(), 0)
            self.assertEqual(order.getRemaining(), 3)

        # The order should now get filled since there is enough volume.
        brk.onBars(*barsBuilder.nextTuple(10, 15, 8, 12, volume=12))
        for order in orders:
            self.assertTrue(order.isFilled())
            self.assertEqual(order.getFilled(), 3)
            self.assertEqual(order.getRemaining(), 0)

    def testVolumeLimitTradeBars(self):
        brk = backtesting.Broker(1000, barFeed=barfeed.BaseBarFeed(bar.Frequency.TRADE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.TRADE)
        orders = []

        # Try with different order types.
        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 3)
        brk.placeOrder(order)
        orders.append(order)
        order = brk.createLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 10, 3)
        brk.placeOrder(order)
        orders.append(order)
        order = brk.createStopOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 10, 3)
        brk.placeOrder(order)
        orders.append(order)
        order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 10, 10, 3)
        brk.placeOrder(order)
        orders.append(order)

        for order in orders:
            self.assertEqual(order.getFilled(), 0)
            self.assertEqual(order.getRemaining(), 3)

        # The orders should not get filled if there is not enough volume.
        brk.onBars(*barsBuilder.nextTuple(10, 15, 8, 12, volume=2))
        for order in orders:
            self.assertFalse(order.isFilled())
            self.assertEqual(order.getFilled(), 0)
            self.assertEqual(order.getRemaining(), 3)

        # The order should now get filled since the volume matches the bar.
        brk.onBars(*barsBuilder.nextTuple(10, 15, 8, 12, volume=3))
        for order in orders:
            self.assertTrue(order.isFilled())
            self.assertEqual(order.getFilled(), 3)
            self.assertEqual(order.getRemaining(), 0)

    def testCancelationEvent(self):
        orderStates = []

        def onOrderEvent(broker, orderEvent):
            orderStates.append(order.getState())

        brk = backtesting.Broker(1000, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk.getOrderUpdatedEvent().subscribe(onOrderEvent)

        order = brk.createLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 2, 1)
        brk.placeOrder(order)

        brk.onBars(*barsBuilder.nextTuple(10, 15, 8, 12))
        # Check that cancelation event gets emited right away.
        brk.cancelOrder(order)
        self.assertTrue(broker.Order.State.CANCELED in orderStates)

    def testSkipOrderSubmittedDuringEvent(self):
        brk = backtesting.Broker(1000, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        ordersUpdated = []

        def onOrderEvent(broker_, orderEvent):
            ordersUpdated.append(orderEvent.getOrder())
            newOrder = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
            brk.placeOrder(newOrder)

        brk.getOrderUpdatedEvent().subscribe(onOrderEvent)

        firstOrder = brk.createLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 2, 1)
        brk.placeOrder(firstOrder)
        self.assertEquals(len(ordersUpdated), 0)

        brk.onBars(*barsBuilder.nextTuple(10, 15, 8, 12))
        self.assertEquals(len(ordersUpdated), 1) # First order got accepted.
        self.assertTrue(firstOrder in ordersUpdated)
        self.assertEquals(len(brk.getActiveOrders()), 2) # Both orders are active.
        # Check that the first one was accepted, and the second one submitted.
        for activeOrder in brk.getActiveOrders():
            if activeOrder.getId() == firstOrder.getId():
                self.assertTrue(activeOrder.isAccepted())
            else:
                self.assertTrue(activeOrder.isSubmitted())

        # Second order should get accepted and filled.
        brk.onBars(*barsBuilder.nextTuple(10, 15, 8, 12))
        self.assertEquals(len(ordersUpdated), 3) 
        self.assertTrue(firstOrder.isAccepted())

class MarketOrderTestCase(BaseTestCase):
    def testBuyAndSell(self):
        brk = backtesting.Broker(11, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Buy
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.onBars(*barsBuilder.nextTuple(10, 15, 8, 12))
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getPrice() == 10)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 1)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
        self.assertTrue(cb.eventCount == 2)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

        # Sell
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        order = brk.createMarketOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.placeOrder(order)
        brk.onBars(*barsBuilder.nextTuple(10, 15, 8, 12))
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getPrice() == 10)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 11)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
        self.assertTrue(cb.eventCount == 2)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

    def testFailToBuy(self):
        brk = backtesting.Broker(5, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)

        # Fail to buy. No money.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.onBars(*barsBuilder.nextTuple(10, 15, 8, 12, sessionClose=True))
        self.assertTrue(order.isAccepted())
        self.assertTrue(order.getExecutionInfo() is None)
        self.assertTrue(len(brk.getActiveOrders()) == 1)
        self.assertTrue(brk.getCash() == 5)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
        self.assertTrue(cb.eventCount == 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Fail to buy. No money. Canceled due to session close.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        brk.onBars(*barsBuilder.nextTuple(11, 15, 8, 12))
        self.assertTrue(order.isCanceled())
        self.assertTrue(order.getExecutionInfo() is None)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 5)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
        self.assertTrue(cb.eventCount == 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

    def testBuy_GTC(self):
        brk = backtesting.Broker(5, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
        order.setGoodTillCanceled(True)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Fail to buy. No money.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        brk.placeOrder(order)
        # Set sessionClose to true test that the order doesn't get canceled.
        brk.onBars(*barsBuilder.nextTuple(10, 15, 8, 12, sessionClose=True))
        self.assertTrue(order.isAccepted())
        self.assertTrue(order.getExecutionInfo() is None)
        self.assertTrue(len(brk.getActiveOrders()) == 1)
        self.assertTrue(brk.getCash() == 5)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
        self.assertTrue(cb.eventCount == 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Buy
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        brk.onBars(*barsBuilder.nextTuple(2, 15, 1, 12))
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getPrice() == 2)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 3)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
        self.assertTrue(cb.eventCount == 1)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

    def testBuyAndSellInTwoSteps(self):
        brk = backtesting.Broker(20.4, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Buy
        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 2)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 2)
        brk.onBars(*barsBuilder.nextTuple(10, 15, 8, 12))
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getPrice() == 10)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(round(brk.getCash(), 1) == 0.4)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 2)
        self.assertEqual(order.getFilled(), 2)
        self.assertEqual(order.getRemaining(), 0)

        # Sell
        order = brk.createMarketOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.onBars(*barsBuilder.nextTuple(10, 15, 8, 12))
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getPrice() == 10)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(round(brk.getCash(), 1) == 10.4)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

        # Sell again
        order = brk.createMarketOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.placeOrder(order)
        brk.onBars(*barsBuilder.nextTuple(11, 15, 8, 12))
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getPrice() == 11)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(round(brk.getCash(), 1) == 21.4)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

    def testPortfolioValue(self):
        brk = backtesting.Broker(11, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Buy
        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.onBars(*barsBuilder.nextTuple(10, 15, 8, 12))
        self.assertTrue(order.isFilled())
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 1)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

        self.assertTrue(brk.getEquityWithBars(barsBuilder.nextBars(11, 11, 11, 11)) == 11 + 1)
        self.assertTrue(brk.getEquityWithBars(barsBuilder.nextBars(1, 1, 1, 1)) == 1 + 1)

    def testBuyWithCommission(self):
        brk = backtesting.Broker(1020, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE), commission=backtesting.FixedPerTrade(10))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Buy
        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 100)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 100)
        brk.onBars(*barsBuilder.nextTuple(10, 15, 8, 12, volume=500))
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getCommission() == 10)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 10)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 100)
        self.assertEqual(order.getFilled(), 100)
        self.assertEqual(order.getRemaining(), 0)

    def testSellShort_1(self):
        brk = backtesting.Broker(1000, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Short sell
        order = brk.createMarketOrder(broker.Order.Action.SELL_SHORT, BaseTestCase.TestInstrument, 1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.onBars(*barsBuilder.nextTuple(200, 200, 200, 200))
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 1200)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == -1)
        self.assertTrue(brk.getEquityWithBars(barsBuilder.nextBars(100, 100, 100, 100)) == 1000 + 100)
        self.assertTrue(brk.getEquityWithBars(barsBuilder.nextBars(0, 0, 0, 0)) == 1000 + 200)
        self.assertTrue(brk.getEquityWithBars(barsBuilder.nextBars(30, 30, 30, 30)) == 1000 + 170)

        # Buy at the same price.
        order = brk.createMarketOrder(broker.Order.Action.BUY_TO_COVER, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.placeOrder(order)
        brk.onBars(*barsBuilder.nextTuple(200, 200, 200, 200))
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 1000)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)

    def testSellShort_2(self):
        brk = backtesting.Broker(1000, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Short sell 1
        order = brk.createMarketOrder(broker.Order.Action.SELL_SHORT, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.placeOrder(order)
        brk.onBars(*barsBuilder.nextTuple(100, 100, 100, 100))
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(brk.getCash() == 1100)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == -1)
        self.assertTrue(brk.getEquityWithBars(barsBuilder.nextBars(100, 100, 100, 100)) == 1000)
        self.assertTrue(brk.getEquityWithBars(barsBuilder.nextBars(0, 0, 0, 0)) == 1000 + 100)
        self.assertTrue(brk.getEquityWithBars(barsBuilder.nextBars(70, 70, 70, 70)) == 1000 + 30)
        self.assertTrue(brk.getEquityWithBars(barsBuilder.nextBars(200, 200, 200, 200)) == 1000 - 100)

        # Buy 2 and earn 50
        order = brk.createMarketOrder(broker.Order.Action.BUY_TO_COVER, BaseTestCase.TestInstrument, 2)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 2)
        brk.placeOrder(order)
        brk.onBars(*barsBuilder.nextTuple(50, 50, 50, 50))
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertEqual(order.getFilled(), 2)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
        self.assertTrue(brk.getCash() == 1000)  # +50 from short sell operation, -50 from buy operation.
        self.assertTrue(brk.getEquityWithBars(barsBuilder.nextBars(50, 50, 50, 50)) == 1000 + 50)
        self.assertTrue(brk.getEquityWithBars(barsBuilder.nextBars(70, 70, 70, 70)) == 1000 + 50 + 20)

        # Sell 1 and earn 50
        order = brk.createMarketOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.placeOrder(order)
        brk.onBars(*barsBuilder.nextTuple(100, 100, 100, 100))
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
        self.assertTrue(brk.getEquityWithBars(barsBuilder.nextBars(70, 70, 70, 70)) == 1000 + 50 + 50)

    def testSellShort_3(self):
        brk = backtesting.Broker(100, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Buy 1
        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.placeOrder(order)
        brk.onBars(*barsBuilder.nextTuple(100, 100, 100, 100))
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
        self.assertTrue(brk.getCash() == 0)

        # Sell 2
        order = brk.createMarketOrder(broker.Order.Action.SELL_SHORT, BaseTestCase.TestInstrument, 2)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 2)
        brk.placeOrder(order)
        brk.onBars(*barsBuilder.nextTuple(100, 100, 100, 100))
        self.assertEqual(order.getFilled(), 2)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == -1)
        self.assertTrue(brk.getCash() == 200)

        # Buy 1
        order = brk.createMarketOrder(broker.Order.Action.BUY_TO_COVER, BaseTestCase.TestInstrument, 1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.onBars(*barsBuilder.nextTuple(100, 100, 100, 100))
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
        self.assertTrue(brk.getCash() == 100)

    def testSellShortWithCommission(self):
        sharePrice = 100
        commission = 10
        brk = backtesting.Broker(1010, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE), commission=backtesting.FixedPerTrade(commission))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Sell 10 shares
        order = brk.createMarketOrder(broker.Order.Action.SELL_SHORT, BaseTestCase.TestInstrument, 10)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 10)
        brk.placeOrder(order)
        brk.onBars(*barsBuilder.nextTuple(sharePrice, sharePrice, sharePrice, sharePrice))
        self.assertEqual(order.getFilled(), 10)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getCommission() == 10)
        self.assertTrue(brk.getCash() == 2000)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == -10)

        # Buy the 10 shares sold short plus 9 extra
        order = brk.createMarketOrder(broker.Order.Action.BUY_TO_COVER, BaseTestCase.TestInstrument, 19)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 19)
        brk.onBars(*barsBuilder.nextTuple(sharePrice, sharePrice, sharePrice, sharePrice))
        self.assertEqual(order.getFilled(), 19)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getCommission() == 10)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 9)
        self.assertTrue(brk.getCash() == sharePrice - commission)

    def testCancel(self):
        brk = backtesting.Broker(100, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
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
        brk.onBars(*barsBuilder.nextTuple(10, 10, 10, 10))
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.assertTrue(order.isCanceled())


class LimitOrderTestCase(BaseTestCase):
    def testBuyAndSell_HitTargetPrice(self):
        brk = backtesting.Broker(20, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Buy
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        order = brk.createLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 10, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.placeOrder(order)
        brk.onBars(*barsBuilder.nextTuple(12, 15, 8, 12))
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getPrice() == 10)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 10)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
        self.assertTrue(cb.eventCount == 2)

        # Sell
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        order = brk.createLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 15, 1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.onBars(*barsBuilder.nextTuple(10, 17, 8, 10))
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getPrice() == 15)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 25)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
        self.assertTrue(cb.eventCount == 2)

    def testBuyAndSell_GetBetterPrice(self):
        brk = backtesting.Broker(20, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Buy
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        order = brk.createLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 14, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.placeOrder(order)
        brk.onBars(*barsBuilder.nextTuple(12, 15, 8, 12))
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getPrice() == 12)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 8)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
        self.assertTrue(cb.eventCount == 2)

        # Sell
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        order = brk.createLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 15, 1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.onBars(*barsBuilder.nextTuple(16, 17, 8, 10))
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getPrice() == 16)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 24)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
        self.assertTrue(cb.eventCount == 2)

    def testBuyAndSell_GappingBars(self):
        brk = backtesting.Broker(20, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Buy. Bar is below the target price.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        order = brk.createLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 20, 1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.onBars(*barsBuilder.nextTuple(10, 15, 8, 10))
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getPrice() == 10)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 10)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
        self.assertTrue(cb.eventCount == 2)

        # Sell. Bar is above the target price.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        order = brk.createLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 30, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.placeOrder(order)
        brk.onBars(*barsBuilder.nextTuple(35, 40, 32, 35))
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getPrice() == 35)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 45)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
        self.assertTrue(cb.eventCount == 2)

    def testFailToBuy(self):
        brk = backtesting.Broker(5, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        order = brk.createLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 5, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Fail to buy (couldn't get specific price).
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        brk.placeOrder(order)
        brk.onBars(*barsBuilder.nextTuple(10, 15, 8, 12, sessionClose=True))
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.assertTrue(order.isAccepted())
        self.assertTrue(order.getExecutionInfo() is None)
        self.assertTrue(len(brk.getActiveOrders()) == 1)
        self.assertTrue(brk.getCash() == 5)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
        self.assertTrue(cb.eventCount == 1)

        # Fail to buy (couldn't get specific price). Canceled due to session close.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        brk.onBars(*barsBuilder.nextTuple(11, 15, 8, 12))
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.assertTrue(order.isCanceled())
        self.assertTrue(order.getExecutionInfo() is None)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 5)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
        self.assertTrue(cb.eventCount == 1)

    def testBuy_GTC(self):
        brk = backtesting.Broker(10, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        order = brk.createLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 4, 2)
        order.setGoodTillCanceled(True)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 2)

        # Fail to buy (couldn't get specific price).
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        brk.placeOrder(order)
        # Set sessionClose to true test that the order doesn't get canceled.
        brk.onBars(*barsBuilder.nextTuple(10, 15, 8, 12, sessionClose=True))
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 2)
        self.assertTrue(order.isAccepted())
        self.assertTrue(order.getExecutionInfo() is None)
        self.assertTrue(len(brk.getActiveOrders()) == 1)
        self.assertTrue(brk.getCash() == 10)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
        self.assertTrue(cb.eventCount == 1)

        # Buy
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        brk.onBars(*barsBuilder.nextTuple(2, 15, 1, 12))
        self.assertEqual(order.getFilled(), 2)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getPrice() == 2)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 6)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 2)
        self.assertTrue(cb.eventCount == 1)


class StopOrderTestCase(BaseTestCase):
    def testLongPosStopLoss(self):
        brk = backtesting.Broker(15, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Buy
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.placeOrder(order)
        brk.onBars(*barsBuilder.nextTuple(10, 15, 8, 12))
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.getExecutionInfo().getPrice() == 10)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 5)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
        self.assertTrue(cb.eventCount == 2)

        # Create stop loss order.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        order = brk.createStopOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 9, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.placeOrder(order)
        brk.onBars(*barsBuilder.nextTuple(10, 15, 10, 12))  # Stop loss not hit.
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.assertFalse(order.isFilled())
        self.assertTrue(len(brk.getActiveOrders()) == 1)
        self.assertTrue(brk.getCash() == 5)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
        self.assertTrue(cb.eventCount == 1)
        brk.onBars(*barsBuilder.nextTuple(10, 15, 8, 12))  # Stop loss hit.
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getPrice() == 9)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 5+9)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
        self.assertTrue(cb.eventCount == 2)

    def testLongPosStopLoss_GappingBars(self):
        brk = backtesting.Broker(15, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Buy
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.placeOrder(order)
        brk.onBars(*barsBuilder.nextTuple(10, 15, 8, 12))
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.getExecutionInfo().getPrice() == 10)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 5)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
        self.assertTrue(cb.eventCount == 2)

        # Create stop loss order.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        order = brk.createStopOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 9, 1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.onBars(*barsBuilder.nextTuple(10, 15, 10, 12))  # Stop loss not hit.
        self.assertFalse(order.isFilled())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.assertTrue(len(brk.getActiveOrders()) == 1)
        self.assertTrue(brk.getCash() == 5)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
        self.assertTrue(cb.eventCount == 1)
        brk.onBars(*barsBuilder.nextTuple(5, 8, 4, 7))  # Stop loss hit.
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.getExecutionInfo().getPrice() == 5)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 5+5)  # Fill the stop loss order at open price.
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
        self.assertTrue(cb.eventCount == 2)

    def testShortPosStopLoss(self):
        brk = backtesting.Broker(15, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Sell short
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        order = brk.createMarketOrder(broker.Order.Action.SELL_SHORT, BaseTestCase.TestInstrument, 1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.onBars(*barsBuilder.nextTuple(10, 15, 8, 12))
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.getExecutionInfo().getPrice() == 10)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 15+10)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == -1)
        self.assertTrue(cb.eventCount == 2)

        # Create stop loss order.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        order = brk.createStopOrder(broker.Order.Action.BUY_TO_COVER, BaseTestCase.TestInstrument, 11, 1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.onBars(*barsBuilder.nextTuple(8, 10, 7, 9))  # Stop loss not hit.
        self.assertFalse(order.isFilled())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.assertTrue(len(brk.getActiveOrders()) == 1)
        self.assertTrue(brk.getCash() == 15+10)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == -1)
        self.assertTrue(cb.eventCount == 1)
        brk.onBars(*barsBuilder.nextTuple(10, 15, 8, 12))  # Stop loss hit.
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.getExecutionInfo().getPrice() == 11)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 15-1)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
        self.assertTrue(cb.eventCount == 2)

    def testShortPosStopLoss_GappingBars(self):
        brk = backtesting.Broker(15, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Sell short
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        order = brk.createMarketOrder(broker.Order.Action.SELL_SHORT, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.placeOrder(order)
        brk.onBars(*barsBuilder.nextTuple(10, 15, 8, 12))
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.getExecutionInfo().getPrice() == 10)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 15+10)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == -1)
        self.assertTrue(cb.eventCount == 2)

        # Create stop loss order.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        order = brk.createStopOrder(broker.Order.Action.BUY_TO_COVER, BaseTestCase.TestInstrument, 11, 1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.onBars(*barsBuilder.nextTuple(8, 10, 7, 9))  # Stop loss not hit.
        self.assertFalse(order.isFilled())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.assertTrue(len(brk.getActiveOrders()) == 1)
        self.assertTrue(brk.getCash() == 15+10)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == -1)
        self.assertTrue(cb.eventCount == 1)
        brk.onBars(*barsBuilder.nextTuple(15, 20, 13, 14))  # Stop loss hit.
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.getExecutionInfo().getPrice() == 15)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 15-5)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
        self.assertTrue(cb.eventCount == 2)


class StopLimitOrderTestCase(BaseTestCase):
    def testFillOpen(self):
        brk = backtesting.Broker(15, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Buy. Stop >= 10. Buy <= 12.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, stopPrice=10, limitPrice=12, quantity=1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price not hit. Limit price not hit.
        brk.onBars(*barsBuilder.nextTuple(8, 9, 7, 8))
        self.assertFalse(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price not hit.
        brk.onBars(*barsBuilder.nextTuple(13, 15, 13, 14))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Limit price hit (bars include the price). Fill at open price.
        brk.onBars(*barsBuilder.nextTuple(11, 15, 10, 14))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getPrice() == 11)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

        # Sell. Stop <= 8. Sell >= 6.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        order = brk.createStopLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, stopPrice=8, limitPrice=6, quantity=1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price not hit. Limit price not hit.
        brk.onBars(*barsBuilder.nextTuple(9, 10, 9, 10))
        self.assertFalse(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price not hit.
        brk.onBars(*barsBuilder.nextTuple(4, 5, 3, 4))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Limit price hit (bars include the price). Fill at open price.
        brk.onBars(*barsBuilder.nextTuple(7, 8, 6, 7))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getPrice() == 7)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

    def testFillOpen_GappingBars(self):
        brk = backtesting.Broker(15, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Buy. Stop >= 10. Buy <= 12.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, stopPrice=10, limitPrice=12, quantity=1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price not hit. Limit price not hit.
        brk.onBars(*barsBuilder.nextTuple(8, 9, 7, 8))
        self.assertFalse(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price not hit.
        brk.onBars(*barsBuilder.nextTuple(13, 18, 13, 17))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Limit price hit (bars don't include the price). Fill at open price.
        brk.onBars(*barsBuilder.nextTuple(7, 9, 6, 8))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getPrice() == 7)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

        # Sell. Stop <= 8. Sell >= 6.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        order = brk.createStopLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, stopPrice=8, limitPrice=6, quantity=1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price not hit. Limit price not hit.
        brk.onBars(*barsBuilder.nextTuple(9, 10, 9, 10))
        self.assertFalse(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price not hit.
        brk.onBars(*barsBuilder.nextTuple(4, 5, 3, 4))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Limit price hit (bars don't include the price). Fill at open price.
        brk.onBars(*barsBuilder.nextTuple(10, 12, 8, 10))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getPrice() == 10)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

    def testFillLimit(self):
        brk = backtesting.Broker(15, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Buy. Stop >= 10. Buy <= 12.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, stopPrice=10, limitPrice=12, quantity=1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price not hit. Limit price not hit.
        brk.onBars(*barsBuilder.nextTuple(8, 9, 7, 8))
        self.assertFalse(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price not hit.
        brk.onBars(*barsBuilder.nextTuple(13, 15, 13, 14))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Limit price hit. Fill at limit price.
        brk.onBars(*barsBuilder.nextTuple(13, 15, 10, 14))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getPrice() == 12)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

        # Sell. Stop <= 8. Sell >= 6.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        order = brk.createStopLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, stopPrice=8, limitPrice=6, quantity=1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price not hit. Limit price not hit.
        brk.onBars(*barsBuilder.nextTuple(9, 10, 9, 10))
        self.assertFalse(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price not hit.
        brk.onBars(*barsBuilder.nextTuple(4, 5, 3, 4))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Limit price hit. Fill at limit price.
        brk.onBars(*barsBuilder.nextTuple(5, 7, 5, 6))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getPrice() == 6)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

    def testHitStopAndLimit(self):
        brk = backtesting.Broker(15, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Buy. Stop >= 10. Buy <= 12.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, stopPrice=10, limitPrice=12, quantity=1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price hit. Fill at stop price.
        brk.onBars(*barsBuilder.nextTuple(9, 15, 8, 14))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getPrice() == 10)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

        # Sell. Stop <= 8. Sell >= 6.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        order = brk.createStopLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, stopPrice=8, limitPrice=6, quantity=1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price hit. Fill at stop price.
        brk.onBars(*barsBuilder.nextTuple(9, 10, 5, 8))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getPrice() == 8)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

    def testInvertedPrices_FillOpen(self):
        brk = backtesting.Broker(15, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Buy. Stop >= 12. Buy <= 10.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, stopPrice=12, limitPrice=10, quantity=1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price not hit. Limit price not hit.
        brk.onBars(*barsBuilder.nextTuple(8, 9, 7, 8))
        self.assertFalse(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price not hit.
        brk.onBars(*barsBuilder.nextTuple(11, 12, 10.5, 11))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Limit price hit. Fill at open price.
        brk.onBars(*barsBuilder.nextTuple(9, 15, 8, 14))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getPrice() == 9)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

        # Sell. Stop <= 6. Sell >= 8.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        order = brk.createStopLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, stopPrice=6, limitPrice=8, quantity=1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price not hit. Limit price not hit.
        brk.onBars(*barsBuilder.nextTuple(9, 10, 9, 10))
        self.assertFalse(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price not hit.
        brk.onBars(*barsBuilder.nextTuple(7, 7, 6, 7))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Limit price hit. Fill at open price.
        brk.onBars(*barsBuilder.nextTuple(9, 10, 8, 9))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getPrice() == 9)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

    def testInvertedPrices_FillOpen_GappingBars(self):
        brk = backtesting.Broker(15, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Buy. Stop >= 12. Buy <= 10.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, stopPrice=12, limitPrice=10, quantity=1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price not hit. Limit price not hit.
        brk.onBars(*barsBuilder.nextTuple(8, 9, 7, 8))
        self.assertFalse(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price not hit.
        brk.onBars(*barsBuilder.nextTuple(11, 12, 10.5, 11))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Limit price hit. Fill at open price.
        brk.onBars(*barsBuilder.nextTuple(7, 9, 6, 8))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getPrice() == 7)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

        # Sell. Stop <= 6. Sell >= 8.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        order = brk.createStopLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, stopPrice=6, limitPrice=8, quantity=1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price not hit. Limit price not hit.
        brk.onBars(*barsBuilder.nextTuple(9, 10, 9, 10))
        self.assertFalse(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price not hit.
        brk.onBars(*barsBuilder.nextTuple(7, 7, 6, 7))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Limit price hit. Fill at open price.
        brk.onBars(*barsBuilder.nextTuple(10, 10, 9, 9))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getPrice() == 10)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

    def testInvertedPrices_FillLimit(self):
        brk = backtesting.Broker(15, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Buy. Stop >= 12. Buy <= 10.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, stopPrice=12, limitPrice=10, quantity=1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price not hit. Limit price not hit.
        brk.onBars(*barsBuilder.nextTuple(8, 9, 7, 8))
        self.assertFalse(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price not hit.
        brk.onBars(*barsBuilder.nextTuple(11, 12, 10.5, 11))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Limit price hit. Fill at limit price.
        brk.onBars(*barsBuilder.nextTuple(11, 13, 8, 9))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getPrice() == 10)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

        # Sell. Stop <= 6. Sell >= 8.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        order = brk.createStopLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, stopPrice=6, limitPrice=8, quantity=1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price not hit. Limit price not hit.
        brk.onBars(*barsBuilder.nextTuple(9, 10, 9, 10))
        self.assertFalse(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price not hit.
        brk.onBars(*barsBuilder.nextTuple(7, 7, 6, 7))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Limit price hit. Fill at limit price.
        brk.onBars(*barsBuilder.nextTuple(7, 10, 6, 9))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getPrice() == 8)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

    def testInvertedPrices_HitStopAndLimit(self):
        brk = backtesting.Broker(15, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Buy. Stop >= 12. Buy <= 10.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, stopPrice=12, limitPrice=10, quantity=1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price hit. Fill at limit price.
        brk.onBars(*barsBuilder.nextTuple(9, 15, 8, 14))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getPrice() == 10)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

        # Sell. Stop <= 6. Sell >= 8.
        cb = Callback()
        brk.getOrderUpdatedEvent().subscribe(cb.onOrderEvent)
        order = brk.createStopLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, stopPrice=6, limitPrice=8, quantity=1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price hit. Fill at limit price.
        brk.onBars(*barsBuilder.nextTuple(6, 10, 5, 7))
        self.assertTrue(order.isLimitOrderActive())
        self.assertTrue(order.isFilled())
        self.assertTrue(order.getExecutionInfo().getPrice() == 8)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
