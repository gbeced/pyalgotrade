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

from . import common

from pyalgotrade import broker
from pyalgotrade.broker import backtesting
from pyalgotrade import bar
from pyalgotrade import barfeed


class OrderUpdateCallback:
    def __init__(self, broker_):
        self.eventCount = 0
        self.events = []
        broker_.getOrderUpdatedEvent().subscribe(self.onOrderEvent)

    def onOrderEvent(self, broker_, orderEvent):
        self.eventCount += 1
        self.events.append(orderEvent)


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

    def getCurrentDateTime(self):
        return self.__nextDateTime

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
        ret = {self.__instrument: bar_}
        self.advance(sessionClose)
        return bar.Bars(ret)

    # sessionClose is True if the next bars should start at a different date.
    def nextBar(self, openPrice, highPrice, lowPrice, closePrice, volume=None, sessionClose=False):
        return self.nextBars(openPrice, highPrice, lowPrice, closePrice, volume, sessionClose)[self.__instrument]

    # sessionClose is True if the next bars should start at a different date.
    def nextTuple(self, openPrice, highPrice, lowPrice, closePrice, volume=None, sessionClose=False):
        ret = self.nextBars(openPrice, highPrice, lowPrice, closePrice, volume, sessionClose)
        return (ret.getDateTime(), ret)


class DecimalTraits(broker.InstrumentTraits):
    def __init__(self, decimals):
        self.__decimals = decimals

    def roundQuantity(self, quantity):
        return round(quantity, self.__decimals)


class BarFeed(barfeed.BaseBarFeed):
    def __init__(self, instrument, frequency):
        barfeed.BaseBarFeed.__init__(self, frequency)
        self.__builder = BarsBuilder(instrument, frequency)
        self.__nextBars = None

    def getCurrentDateTime(self):
        return self.__builder.getCurrentDateTime()

    def start(self):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()

    def join(self):
        raise NotImplementedError()

    def eof(self):
        raise NotImplementedError()

    def peekDateTime(self):
        raise NotImplementedError()

    def dispatchBars(self, openPrice, highPrice, lowPrice, closePrice, volume=None, sessionClose=False):
        self.__nextBars = self.__builder.nextBars(openPrice, highPrice, lowPrice, closePrice, volume, sessionClose)
        self.dispatch()

    def barsHaveAdjClose(self):
        raise True

    def getNextBars(self):
        return self.__nextBars


class BaseTestCase(common.TestCase):
    TestInstrument = "orcl"

    def buildBroker(self, *args, **kwargs):
        return backtesting.Broker(*args, **kwargs)

    def buildBarFeed(self, *args, **kwargs):
        return BarFeed(*args, **kwargs)


class CommissionTestCase(common.TestCase):
    def testNoCommission(self):
        comm = backtesting.NoCommission()
        self.assertEqual(comm.calculate(None, 1, 1), 0)

    def testFixedPerTrade(self):
        comm = backtesting.FixedPerTrade(1.2)
        order = backtesting.MarketOrder(broker.Order.Action.BUY, "orcl", 1, False, broker.IntegerTraits())
        self.assertEqual(comm.calculate(order, 1, 1), 1.2)

    def testTradePercentage(self):
        comm = backtesting.TradePercentage(0.1)
        self.assertEqual(comm.calculate(None, 1, 1), 0.1)
        self.assertEqual(comm.calculate(None, 2, 2), 0.4)


class BrokerTestCase(BaseTestCase):
    def testOneCancelsAnother(self):
        orders = {}

        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(1000, barFeed)

        def onOrderEvent(broker_, orderEvent):
            if orderEvent.getEventType() == broker.OrderEvent.Type.FILLED and orderEvent.getOrder().getId() == orders["sell"].getId():
                brk.cancelOrder(orders["stoploss"])

        # Buy order.
        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())

        barFeed.dispatchBars(10, 15, 8, 12)
        self.assertTrue(order.isFilled())

        brk.getOrderUpdatedEvent().subscribe(onOrderEvent)

        # Create a sell limit and a stop loss order.
        order = brk.createLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 11, 1)
        orders["sell"] = order
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        order = brk.createStopOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 8, 1)
        orders["stoploss"] = order
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        barFeed.dispatchBars(10, 15, 5, 12)

        # Only one order (the sell limit order) should have got filled. The other one should be canceled.
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 0)
        self.assertTrue(orders["sell"].isFilled())
        self.assertTrue(orders["stoploss"].isCanceled())

    def testRegressionGetActiveOrders(self):
        activeOrders = []

        def onOrderEvent(brk, orderEvent):
            if orderEvent.getEventType() != broker.OrderEvent.Type.SUBMITTED:
                activeOrders.append(len(brk.getActiveOrders()))

        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(1000, barFeed)

        brk.getOrderUpdatedEvent().subscribe(onOrderEvent)
        o1 = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
        self.assertEqual(o1.getSubmitDateTime(), None)
        brk.submitOrder(o1)
        self.assertEqual(o1.getSubmitDateTime(), barFeed.getCurrentDateTime())
        o2 = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
        self.assertEqual(o2.getSubmitDateTime(), None)
        brk.submitOrder(o2)
        self.assertEqual(o2.getSubmitDateTime(), barFeed.getCurrentDateTime())

        self.assertEqual(o1.getFilled(), 0)
        self.assertEqual(o2.getFilled(), 0)
        self.assertEqual(o1.getRemaining(), o1.getQuantity())
        self.assertEqual(o2.getRemaining(), o2.getQuantity())

        barFeed.dispatchBars(10, 15, 8, 12)

        self.assertNotEqual(o1.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertNotEqual(o2.getSubmitDateTime(), barFeed.getCurrentDateTime())

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
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(1000, barFeed)

        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 3)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 3)

        # The order should not get filled if there is not enough volume.
        barFeed.dispatchBars(10, 15, 8, 12, volume=3)
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 3)

        # The order should now get filled since there is enough volume.
        barFeed.dispatchBars(10, 15, 8, 12, volume=12)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 3)
        self.assertEqual(order.getRemaining(), 0)

    def testVolumeLimitTradeBars(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.TRADE)
        brk = self.buildBroker(1000, barFeed)

        # Try with different order types.
        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 3)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 3)

        # The order should get partially filled.
        barFeed.dispatchBars(10, 15, 8, 12, volume=1)
        self.assertTrue(order.isPartiallyFilled())
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 2)

        # The order should now get completely filled.
        barFeed.dispatchBars(10, 15, 8, 12, volume=3)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 3)
        self.assertEqual(order.getRemaining(), 0)

    def testCancelationEvent(self):
        orderStates = []

        def onOrderEvent(broker, orderEvent):
            orderStates.append(order.getState())

        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(1000, barFeed)
        brk.getOrderUpdatedEvent().subscribe(onOrderEvent)

        order = brk.createLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 2, 1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())

        barFeed.dispatchBars(10, 15, 8, 12)
        # Check that cancelation event gets emited right away.
        brk.cancelOrder(order)
        self.assertTrue(broker.Order.State.CANCELED in orderStates)

    def testSkipOrderSubmittedDuringEvent(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(1000, barFeed)
        ordersUpdated = []

        def onOrderEvent(broker_, orderEvent):
            if orderEvent.getEventType() != broker.OrderEvent.Type.SUBMITTED:
                ordersUpdated.append(orderEvent.getOrder())
                newOrder = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
                self.assertEqual(newOrder.getSubmitDateTime(), None)
                brk.submitOrder(newOrder)
                self.assertEqual(newOrder.getSubmitDateTime(), barFeed.getCurrentDateTime())

        brk.getOrderUpdatedEvent().subscribe(onOrderEvent)

        # The first order gets submitted.
        firstOrder = brk.createLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 2, 1)
        self.assertEqual(firstOrder.getSubmitDateTime(), None)
        brk.submitOrder(firstOrder)
        self.assertEqual(firstOrder.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(len(ordersUpdated), 0)

        # The first order gets accepted, and the second one gets submitted..
        barFeed.dispatchBars(10, 15, 8, 12)
        self.assertEqual(len(ordersUpdated), 1)  # First order got accepted.
        self.assertTrue(firstOrder in ordersUpdated)
        self.assertEqual(len(brk.getActiveOrders()), 2)  # Both orders are active.
        # Check that the first one was accepted, and the second one submitted.
        for activeOrder in brk.getActiveOrders():
            if activeOrder.getId() == firstOrder.getId():
                self.assertTrue(activeOrder.isAccepted())
            else:
                self.assertTrue(activeOrder.isSubmitted())

        # Second order should get accepted and filled.
        barFeed.dispatchBars(10, 15, 8, 12)
        self.assertEqual(len(ordersUpdated), 3)
        self.assertTrue(firstOrder.isAccepted())

    def testPartialFillAndCancel(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.DAY)
        brk = self.buildBroker(1000, barFeed)
        cb = OrderUpdateCallback(brk)

        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 10)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())

        # 2 should get filled.
        barFeed.dispatchBars(12, 15, 8, 12, 10)
        self.assertTrue(order.isCanceled())
        self.assertEqual(order.getFilled(), 2)
        self.assertEqual(order.getRemaining(), 8)
        self.assertEqual(order.getAvgFillPrice(), 12)
        self.assertEqual(order.getExecutionInfo().getPrice(), 12)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 2)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        self.assertEqual(len(cb.events), 4)
        self.assertEqual(cb.events[0].getEventType(), broker.OrderEvent.Type.SUBMITTED)
        self.assertEqual(cb.events[1].getEventType(), broker.OrderEvent.Type.ACCEPTED)
        self.assertEqual(cb.events[2].getEventType(), broker.OrderEvent.Type.PARTIALLY_FILLED)
        self.assertEqual(cb.events[3].getEventType(), broker.OrderEvent.Type.CANCELED)

    def testVolumeLimitPerBar1(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(1000, barFeed)

        order1 = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 2)
        self.assertEqual(order1.getSubmitDateTime(), None)
        brk.submitOrder(order1)
        self.assertEqual(order1.getSubmitDateTime(), barFeed.getCurrentDateTime())
        order2 = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 2)
        self.assertEqual(order2.getSubmitDateTime(), None)
        brk.submitOrder(order2)
        self.assertEqual(order2.getSubmitDateTime(), barFeed.getCurrentDateTime())

        barFeed.dispatchBars(12, 15, 8, 12, 10)
        # 2 should get filled for the first order.
        self.assertTrue(order1.isFilled())
        self.assertEqual(order1.getFilled(), 2)
        self.assertEqual(order1.getRemaining(), 0)
        self.assertEqual(order1.getAvgFillPrice(), 12)
        self.assertEqual(order1.getExecutionInfo().getPrice(), 12)
        self.assertEqual(order1.getExecutionInfo().getQuantity(), 2)
        self.assertEqual(order1.getExecutionInfo().getCommission(), 0)
        # 0 should get filled for the second order.
        self.assertTrue(order2.isAccepted())
        self.assertEqual(order2.getFilled(), 0)
        self.assertEqual(order2.getRemaining(), 2)
        self.assertEqual(order2.getAvgFillPrice(), None)
        self.assertEqual(order2.getExecutionInfo(), None)

        barFeed.dispatchBars(13, 15, 8, 12, 10)
        # 2 should get filled for the second order.
        self.assertTrue(order2.isFilled())
        self.assertEqual(order2.getFilled(), 2)
        self.assertEqual(order2.getRemaining(), 0)
        self.assertEqual(order2.getAvgFillPrice(), 13)
        self.assertEqual(order2.getExecutionInfo().getPrice(), 13)
        self.assertEqual(order2.getExecutionInfo().getQuantity(), 2)
        self.assertEqual(order2.getExecutionInfo().getCommission(), 0)

    def testVolumeLimitPerBar2(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(1000, barFeed)

        order1 = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order1.getSubmitDateTime(), None)
        brk.submitOrder(order1)
        self.assertEqual(order1.getSubmitDateTime(), barFeed.getCurrentDateTime())
        order2 = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order2.getSubmitDateTime(), None)
        brk.submitOrder(order2)
        self.assertEqual(order2.getSubmitDateTime(), barFeed.getCurrentDateTime())

        barFeed.dispatchBars(12, 15, 8, 12, 10)
        # 1 should get filled for the first order.
        self.assertTrue(order1.isFilled())
        self.assertEqual(order1.getFilled(), 1)
        self.assertEqual(order1.getRemaining(), 0)
        self.assertEqual(order1.getAvgFillPrice(), 12)
        self.assertEqual(order1.getExecutionInfo().getPrice(), 12)
        self.assertEqual(order1.getExecutionInfo().getQuantity(), 1)
        self.assertEqual(order1.getExecutionInfo().getCommission(), 0)
        # 1 should get filled for the second order.
        self.assertTrue(order2.isFilled())
        self.assertEqual(order2.getFilled(), 1)
        self.assertEqual(order2.getRemaining(), 0)
        self.assertEqual(order2.getAvgFillPrice(), 12)
        self.assertEqual(order2.getExecutionInfo().getPrice(), 12)
        self.assertEqual(order2.getExecutionInfo().getQuantity(), 1)
        self.assertEqual(order2.getExecutionInfo().getCommission(), 0)

    def testGetActiveOrders(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(1000, barFeed)

        order1 = brk.createMarketOrder(broker.Order.Action.BUY, "ins1", 1)
        self.assertEqual(order1.getSubmitDateTime(), None)
        brk.submitOrder(order1)
        self.assertEqual(order1.getSubmitDateTime(), barFeed.getCurrentDateTime())
        order2 = brk.createMarketOrder(broker.Order.Action.BUY, "ins2", 1)
        self.assertEqual(order2.getSubmitDateTime(), None)
        brk.submitOrder(order2)
        self.assertEqual(order2.getSubmitDateTime(), barFeed.getCurrentDateTime())

        self.assertEqual(len(brk.getActiveOrders()), 2)
        self.assertEqual(len(brk.getActiveOrders("ins1")), 1)
        self.assertEqual(len(brk.getActiveOrders("ins2")), 1)
        self.assertEqual(len(brk.getActiveOrders("ins3")), 0)


class MarketOrderTestCase(BaseTestCase):
    def testGetPositions(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        cash = 1000000
        brk = backtesting.Broker(cash, barFeed)

        # Buy
        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
        brk.submitOrder(order)
        barFeed.dispatchBars(12.03, 12.03, 12.03, 12.03, 555.00)
        self.assertTrue(order.isFilled())
        self.assertEqual(brk.getPositions().get(BaseTestCase.TestInstrument), 1)

        # Sell
        order = brk.createMarketOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 1)
        brk.submitOrder(order)
        barFeed.dispatchBars(12.03, 12.03, 12.03, 12.03, 555.00)
        self.assertTrue(order.isFilled())
        self.assertEqual(brk.getPositions().get(BaseTestCase.TestInstrument), None)

    def testBuyPartialWithTwoDecimals(self):
        class Broker(backtesting.Broker):
            def getInstrumentTraits(self, instrument):
                return DecimalTraits(2)

        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        cash = 1000000
        brk = Broker(cash, barFeed)

        # Buy
        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 500)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())

        # 138.75 should get filled.
        barFeed.dispatchBars(12.03, 12.03, 12.03, 12.03, 555.00)
        self.assertTrue(order.isPartiallyFilled())
        self.assertEqual(order.getExecutionInfo().getQuantity(), 138.75)
        self.assertEqual(order.getFilled(), 138.75)
        self.assertEqual(order.getRemaining(), 361.25)
        self.assertEqual(order.getAvgFillPrice(), 12.03)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 138.75)
        self.assertEqual(brk.getEquity(), cash)
        self.assertEqual(brk.getFillStrategy().getVolumeLeft()[BaseTestCase.TestInstrument], 0)

        # 361.25 should get filled.
        barFeed.dispatchBars(12.03, 12.03, 12.03, 12.03, 2345.00)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getQuantity(), 361.25)
        self.assertEqual(order.getFilled(), 500)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getAvgFillPrice(), 12.03)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 500)
        self.assertEqual(brk.getEquity(), cash)
        self.assertEqual(brk.getFillStrategy().getVolumeLeft()[BaseTestCase.TestInstrument], 586.25 - 361.25)

    def testBuyPartialWithEightDecimals(self):
        quantityPresicion = 8
        cashPresicion = 2
        maxFill = 0.25

        class Broker(backtesting.Broker):
            def getInstrumentTraits(self, instrument):
                return DecimalTraits(quantityPresicion)

        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        cash = 1000000
        brk = Broker(cash, barFeed)

        # Buy
        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())

        volumes = [0.0001, 0.1, 0.0000001, 0.00000001, 0.132401]
        volumeFill = [(volume, round(volume*maxFill, quantityPresicion)) for volume in volumes]
        cumFilled = 0
        for volume, expectedFill in volumeFill:
            cumFilled += expectedFill  # I'm not rounding here so I can carry errors.
            barFeed.dispatchBars(12.03, 12.03, 12.03, 12.03, volume)
            # print expectedFill, cumFilled
            self.assertTrue(order.isPartiallyFilled())
            if expectedFill > 0:
                self.assertEqual(order.getExecutionInfo().getQuantity(), expectedFill)
            self.assertEqual(order.getFilled(), round(cumFilled, quantityPresicion))
            self.assertEqual(order.getRemaining(), 1 - cumFilled)
            self.assertEqual(round(order.getAvgFillPrice(), cashPresicion), 12.03)
            self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), round(cumFilled, quantityPresicion))
            self.assertEqual(round(brk.getEquity(), cashPresicion), cash)
            self.assertEqual(round(brk.getFillStrategy().getVolumeLeft()[BaseTestCase.TestInstrument], quantityPresicion), 0)

        # Full fill
        filledSoFar = order.getFilled()
        volume = 10
        cumFilled += expectedFill  # I'm not rounding here so I can carry errors.
        barFeed.dispatchBars(12.03, 12.03, 12.03, 12.03, volume)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getQuantity(), 1 - filledSoFar)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getAvgFillPrice(), 12.03)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 1)
        self.assertEqual(brk.getEquity(), cash)
        self.assertEqual(round(brk.getFillStrategy().getVolumeLeft()[BaseTestCase.TestInstrument], quantityPresicion), round((volume*maxFill) - (1-filledSoFar), quantityPresicion))

    def testBuySellPartial(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(1000, barFeed)

        # Buy
        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 10)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        # 2 should get filled.
        barFeed.dispatchBars(12, 15, 8, 12, 10)
        self.assertTrue(order.isPartiallyFilled())
        self.assertEqual(order.getFilled(), 2)
        self.assertEqual(order.getRemaining(), 8)
        self.assertEqual(order.getAvgFillPrice(), 12)
        self.assertEqual(order.getExecutionInfo().getPrice(), 12)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 2)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        # 5 should get filled.
        barFeed.dispatchBars(13, 15, 8, 12, 20)
        self.assertTrue(order.isPartiallyFilled())
        self.assertEqual(order.getFilled(), 7)
        self.assertEqual(order.getRemaining(), 3)
        self.assertEqual(order.getAvgFillPrice(), (12 * 2 + 13 * 5) / 7.0)
        self.assertEqual(order.getExecutionInfo().getPrice(), 13)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 5)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        # 3 should get filled.
        barFeed.dispatchBars(12, 15, 8, 12, 20)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 10)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getAvgFillPrice(), (12 * 5 + 13 * 5) / 10.0)
        self.assertEqual(order.getExecutionInfo().getPrice(), 12)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 3)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)

        # Sell
        order = brk.createMarketOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 10)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        # 0 should get filled.
        barFeed.dispatchBars(12, 15, 8, 12, 2)
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 10)
        # 1 should get filled.
        barFeed.dispatchBars(12, 15, 8, 12, 4)
        self.assertTrue(order.isPartiallyFilled())
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 9)
        self.assertEqual(order.getAvgFillPrice(), 12)
        self.assertEqual(order.getExecutionInfo().getPrice(), 12)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 1)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        # 9 should get filled.
        barFeed.dispatchBars(12, 15, 8, 12, 100)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 10)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getAvgFillPrice(), 12)
        self.assertEqual(order.getExecutionInfo().getPrice(), 12)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 9)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)

    def testBuyAndSell(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(11, barFeed)

        # Buy
        cb = OrderUpdateCallback(brk)
        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        barFeed.dispatchBars(10, 15, 8, 12)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), 10)
        self.assertTrue(order.getExecutionInfo().getPrice() == 10)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 1)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
        self.assertEqual(cb.eventCount, 3)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

        # Sell
        cb = OrderUpdateCallback(brk)
        order = brk.createMarketOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        barFeed.dispatchBars(10, 15, 8, 12)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), 10)
        self.assertTrue(order.getExecutionInfo().getPrice() == 10)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 11)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
        self.assertEqual(cb.eventCount, 3)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

    def testFailToBuy(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(5, barFeed)

        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)

        # Fail to buy. No money.
        cb = OrderUpdateCallback(brk)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        barFeed.dispatchBars(10, 15, 8, 12, sessionClose=True)
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getAvgFillPrice(), None)
        self.assertTrue(order.getExecutionInfo() is None)
        self.assertTrue(len(brk.getActiveOrders()) == 1)
        self.assertTrue(brk.getCash() == 5)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
        self.assertEqual(cb.eventCount, 2)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Fail to buy. No money. Canceled due to session close.
        cb = OrderUpdateCallback(brk)
        barFeed.dispatchBars(11, 15, 8, 12)
        self.assertTrue(order.isCanceled())
        self.assertEqual(order.getAvgFillPrice(), None)
        self.assertTrue(order.getExecutionInfo() is None)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 5)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
        self.assertTrue(cb.eventCount == 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

    def testBuy_GTC(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(5, barFeed)

        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
        order.setGoodTillCanceled(True)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Fail to buy. No money.
        cb = OrderUpdateCallback(brk)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        # Set sessionClose to true test that the order doesn't get canceled.
        barFeed.dispatchBars(10, 15, 8, 12, sessionClose=True)
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getAvgFillPrice(), None)
        self.assertTrue(order.getExecutionInfo() is None)
        self.assertTrue(len(brk.getActiveOrders()) == 1)
        self.assertTrue(brk.getCash() == 5)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
        self.assertEqual(cb.eventCount, 2)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Buy
        cb = OrderUpdateCallback(brk)
        barFeed.dispatchBars(2, 15, 1, 12)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), 2)
        self.assertTrue(order.getExecutionInfo().getPrice() == 2)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 3)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
        self.assertTrue(cb.eventCount == 1)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

    def testBuyAndSellInTwoSteps(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(20.4, barFeed)

        # Buy
        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 2)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 2)
        barFeed.dispatchBars(10, 15, 8, 12)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), 10)
        self.assertTrue(order.getExecutionInfo().getPrice() == 10)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(round(brk.getCash(), 1) == 0.4)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 2)
        self.assertEqual(order.getFilled(), 2)
        self.assertEqual(order.getRemaining(), 0)

        # Sell
        order = brk.createMarketOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        barFeed.dispatchBars(10, 15, 8, 12)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), 10)
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
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        barFeed.dispatchBars(11, 15, 8, 12)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), 11)
        self.assertTrue(order.getExecutionInfo().getPrice() == 11)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(round(brk.getCash(), 1) == 21.4)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

    def testPortfolioValue(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(11, barFeed)

        # Buy
        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        barFeed.dispatchBars(10, 15, 8, 12)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 1)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)

        barFeed.dispatchBars(11, 11, 11, 11)
        self.assertEqual(brk.getEquity(), 11 + 1)
        barFeed.dispatchBars(1, 1, 1, 1)
        self.assertEqual(brk.getEquity(), 1 + 1)

    def testBuyWithCommission(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(1020, barFeed, commission=backtesting.FixedPerTrade(10))

        # Buy
        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 100)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 100)
        barFeed.dispatchBars(10, 15, 8, 12, volume=500)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), 10)
        self.assertTrue(order.getExecutionInfo().getCommission() == 10)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 10)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 100)
        self.assertEqual(order.getFilled(), 100)
        self.assertEqual(order.getRemaining(), 0)

    def testSellShort_1(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(1000, barFeed)

        # Short sell
        order = brk.createMarketOrder(broker.Order.Action.SELL_SHORT, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        barFeed.dispatchBars(200, 200, 200, 200)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), 200)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 1200)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == -1)
        barFeed.dispatchBars(100, 100, 100, 100)
        self.assertTrue(brk.getEquity() == 1000 + 100)
        barFeed.dispatchBars(0, 0, 0, 0)
        self.assertTrue(brk.getEquity() == 1000 + 200)
        barFeed.dispatchBars(30, 30, 30, 30)
        self.assertTrue(brk.getEquity() == 1000 + 170)

        # Buy at the same price.
        order = brk.createMarketOrder(broker.Order.Action.BUY_TO_COVER, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        barFeed.dispatchBars(200, 200, 200, 200)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), 200)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 1000)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)

    def testSellShort_2(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(1000, barFeed)

        # Short sell 1
        order = brk.createMarketOrder(broker.Order.Action.SELL_SHORT, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        barFeed.dispatchBars(100, 100, 100, 100)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getAvgFillPrice(), 100)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(brk.getCash() == 1100)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == -1)
        barFeed.dispatchBars(100, 100, 100, 100)
        self.assertTrue(brk.getEquity() == 1000)
        barFeed.dispatchBars(0, 0, 0, 0)
        self.assertTrue(brk.getEquity() == 1000 + 100)
        barFeed.dispatchBars(70, 70, 70, 70)
        self.assertTrue(brk.getEquity() == 1000 + 30)
        barFeed.dispatchBars(200, 200, 200, 200)
        self.assertTrue(brk.getEquity() == 1000 - 100)

        # Buy 2 and earn 50
        order = brk.createMarketOrder(broker.Order.Action.BUY_TO_COVER, BaseTestCase.TestInstrument, 2)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 2)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        barFeed.dispatchBars(50, 50, 50, 50)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), 50)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertEqual(order.getFilled(), 2)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
        self.assertTrue(brk.getCash() == 1000)  # +50 from short sell operation, -50 from buy operation.
        barFeed.dispatchBars(50, 50, 50, 50)
        self.assertTrue(brk.getEquity() == 1000 + 50)
        barFeed.dispatchBars(70, 70, 70, 70)
        self.assertTrue(brk.getEquity() == 1000 + 50 + 20)

        # Sell 1 and earn 50
        order = brk.createMarketOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        barFeed.dispatchBars(100, 100, 100, 100)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getAvgFillPrice(), 100)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
        barFeed.dispatchBars(70, 70, 70, 70)
        self.assertTrue(brk.getEquity() == 1000 + 50 + 50)

    def testSellShort_3(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(100, barFeed)

        # Buy 1
        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        barFeed.dispatchBars(100, 100, 100, 100)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), 100)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
        self.assertTrue(brk.getCash() == 0)

        # Sell 2
        order = brk.createMarketOrder(broker.Order.Action.SELL_SHORT, BaseTestCase.TestInstrument, 2)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 2)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        barFeed.dispatchBars(100, 100, 100, 100)
        self.assertEqual(order.getFilled(), 2)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), 100)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == -1)
        self.assertTrue(brk.getCash() == 200)

        # Buy 1
        order = brk.createMarketOrder(broker.Order.Action.BUY_TO_COVER, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        barFeed.dispatchBars(100, 100, 100, 100)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getAvgFillPrice(), 100)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
        self.assertTrue(brk.getCash() == 100)

    def testSellShortWithCommission(self):
        sharePrice = 100
        commission = 10
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(1010, barFeed, commission=backtesting.FixedPerTrade(commission))

        # Sell 10 shares
        order = brk.createMarketOrder(broker.Order.Action.SELL_SHORT, BaseTestCase.TestInstrument, 10)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 10)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        barFeed.dispatchBars(sharePrice, sharePrice, sharePrice, sharePrice)
        self.assertEqual(order.getFilled(), 10)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), sharePrice)
        self.assertTrue(order.getExecutionInfo().getCommission() == 10)
        self.assertTrue(brk.getCash() == 2000)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == -10)

        # Buy the 10 shares sold short plus 9 extra
        order = brk.createMarketOrder(broker.Order.Action.BUY_TO_COVER, BaseTestCase.TestInstrument, 19)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 19)
        barFeed.dispatchBars(sharePrice, sharePrice, sharePrice, sharePrice)
        self.assertEqual(order.getFilled(), 19)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), sharePrice)
        self.assertTrue(order.getExecutionInfo().getCommission() == 10)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 9)
        self.assertTrue(brk.getCash() == sharePrice - commission)

    def testCancel(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(100, barFeed)

        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.cancelOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        barFeed.dispatchBars(10, 10, 10, 10)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.assertTrue(order.isCanceled())

    def testTradePercentageWithPartialFills(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(1000, barFeed)
        commPercentage = 0.1
        brk.setCommission(backtesting.TradePercentage(0.1))

        # Buy
        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 10)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getCommissions(), 0)
        # 2 should get filled.
        barFeed.dispatchBars(12, 15, 8, 12, 10)
        self.assertTrue(order.isPartiallyFilled())
        self.assertEqual(order.getFilled(), 2)
        self.assertEqual(order.getRemaining(), 8)
        self.assertEqual(order.getAvgFillPrice(), 12)
        self.assertEqual(order.getCommissions(), 12*2*commPercentage)
        self.assertEqual(order.getExecutionInfo().getPrice(), 12)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 2)
        self.assertEqual(order.getExecutionInfo().getCommission(), 12*2*commPercentage)
        # 5 should get filled.
        barFeed.dispatchBars(12, 15, 8, 12, 20)
        self.assertTrue(order.isPartiallyFilled())
        self.assertEqual(order.getFilled(), 7)
        self.assertEqual(order.getRemaining(), 3)
        self.assertEqual(order.getAvgFillPrice(), 12)
        self.assertEqual(order.getCommissions(), 12*7*commPercentage)
        self.assertEqual(order.getExecutionInfo().getPrice(), 12)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 5)
        self.assertEqual(order.getExecutionInfo().getCommission(), 12*5*commPercentage)
        # 3 should get filled.
        barFeed.dispatchBars(12, 15, 8, 12, 20)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 10)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getAvgFillPrice(), 12)
        self.assertEqual(order.getCommissions(), 12*10*commPercentage)
        self.assertEqual(order.getExecutionInfo().getPrice(), 12)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 3)
        self.assertEqual(order.getExecutionInfo().getCommission(), 12*3*commPercentage)

    def testFixedPerTradeWithPartialFills(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(1000, barFeed)
        brk.setCommission(backtesting.FixedPerTrade(1.2))

        # Buy
        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 10)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getCommissions(), 0)
        # 2 should get filled.
        barFeed.dispatchBars(12, 15, 8, 12, 10)
        self.assertTrue(order.isPartiallyFilled())
        self.assertEqual(order.getFilled(), 2)
        self.assertEqual(order.getRemaining(), 8)
        self.assertEqual(order.getAvgFillPrice(), 12)
        self.assertEqual(order.getCommissions(), 1.2)
        self.assertEqual(order.getExecutionInfo().getPrice(), 12)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 2)
        self.assertEqual(order.getExecutionInfo().getCommission(), 1.2)  # Commision applied in the first fill.
        # 5 should get filled.
        barFeed.dispatchBars(12, 15, 8, 12, 20)
        self.assertTrue(order.isPartiallyFilled())
        self.assertEqual(order.getFilled(), 7)
        self.assertEqual(order.getRemaining(), 3)
        self.assertEqual(order.getAvgFillPrice(), 12)
        self.assertEqual(order.getCommissions(), 1.2)
        self.assertEqual(order.getExecutionInfo().getPrice(), 12)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 5)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        # 3 should get filled.
        barFeed.dispatchBars(12, 15, 8, 12, 20)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 10)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getAvgFillPrice(), 12)
        self.assertEqual(order.getCommissions(), 1.2)
        self.assertEqual(order.getExecutionInfo().getPrice(), 12)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 3)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)

    def testDailyMarketOnClose(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.DAY)
        cash = 1000000
        brk = backtesting.Broker(cash, barFeed)

        # Buy
        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 2, onClose=True)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)

        # 2 should get filled at the closing price.
        barFeed.dispatchBars(12, 15, 8, 14, 10)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 2)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getAvgFillPrice(), 14)
        self.assertEqual(order.getExecutionInfo().getPrice(), 14)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 2)

    def testIntradayMarketOnClose(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        cash = 1000000
        brk = backtesting.Broker(cash, barFeed)

        with self.assertRaisesRegex(Exception, "Market-on-close not supported with intraday feeds"):
            brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1, onClose=True)


class LimitOrderTestCase(BaseTestCase):
    def testBuySellPartial(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(1000, barFeed)

        # Buy
        order = brk.createLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 10, 10)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        # 2 should get filled.
        barFeed.dispatchBars(12, 15, 8, 12, 10)
        self.assertTrue(order.isPartiallyFilled())
        self.assertEqual(order.getFilled(), 2)
        self.assertEqual(order.getRemaining(), 8)
        self.assertEqual(order.getAvgFillPrice(), 10)
        self.assertEqual(order.getExecutionInfo().getPrice(), 10)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 2)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        # 5 should get filled.
        barFeed.dispatchBars(12, 15, 8, 12, 20)
        self.assertTrue(order.isPartiallyFilled())
        self.assertEqual(order.getFilled(), 7)
        self.assertEqual(order.getRemaining(), 3)
        self.assertEqual(order.getAvgFillPrice(), 10)
        self.assertEqual(order.getExecutionInfo().getPrice(), 10)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 5)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        # 3 should get filled.
        barFeed.dispatchBars(12, 15, 8, 12, 20)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 10)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getAvgFillPrice(), 10)
        self.assertEqual(order.getExecutionInfo().getPrice(), 10)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 3)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)

        # Sell
        order = brk.createLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 10, 10)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        # 0 should get filled.
        barFeed.dispatchBars(12, 15, 8, 12, 2)
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 10)
        # 1 should get filled.
        barFeed.dispatchBars(12, 15, 8, 12, 4)
        self.assertTrue(order.isPartiallyFilled())
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 9)
        self.assertEqual(order.getAvgFillPrice(), 12)
        self.assertEqual(order.getExecutionInfo().getPrice(), 12)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 1)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        # 9 should get filled.
        barFeed.dispatchBars(12, 15, 8, 12, 100)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 10)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getAvgFillPrice(), 12)
        self.assertEqual(order.getExecutionInfo().getPrice(), 12)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 9)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)

    def testBuyAndSell_HitTargetPrice(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(20, barFeed)

        # Buy
        cb = OrderUpdateCallback(brk)
        order = brk.createLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 10, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        barFeed.dispatchBars(12, 15, 8, 12)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), 10)
        self.assertTrue(order.getExecutionInfo().getPrice() == 10)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 10)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
        self.assertEqual(cb.eventCount, 3)

        # Sell
        cb = OrderUpdateCallback(brk)
        order = brk.createLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 15, 1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        barFeed.dispatchBars(10, 17, 8, 10)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), 15)
        self.assertTrue(order.getExecutionInfo().getPrice() == 15)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 25)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
        self.assertEqual(cb.eventCount, 3)

    def testBuyAndSell_GetBetterPrice(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(20, barFeed)

        # Buy
        cb = OrderUpdateCallback(brk)
        order = brk.createLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 14, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        barFeed.dispatchBars(12, 15, 8, 12)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), 12)
        self.assertTrue(order.getExecutionInfo().getPrice() == 12)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 8)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
        self.assertEqual(cb.eventCount, 3)

        # Sell
        cb = OrderUpdateCallback(brk)
        order = brk.createLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 15, 1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        barFeed.dispatchBars(16, 17, 8, 10)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), 16)
        self.assertTrue(order.getExecutionInfo().getPrice() == 16)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 24)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
        self.assertEqual(cb.eventCount, 3)

    def testBuyAndSell_GappingBars(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(20, barFeed)

        # Buy. Bar is below the target price.
        cb = OrderUpdateCallback(brk)
        order = brk.createLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 20, 1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        barFeed.dispatchBars(10, 15, 8, 10)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), 10)
        self.assertTrue(order.getExecutionInfo().getPrice() == 10)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 10)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
        self.assertEqual(cb.eventCount, 3)

        # Sell. Bar is above the target price.
        cb = OrderUpdateCallback(brk)
        order = brk.createLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 30, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        barFeed.dispatchBars(35, 40, 32, 35)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), 35)
        self.assertTrue(order.getExecutionInfo().getPrice() == 35)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 45)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
        self.assertEqual(cb.eventCount, 3)

    def testFailToBuy(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(5, barFeed)

        order = brk.createLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 5, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Fail to buy (couldn't get specific price).
        cb = OrderUpdateCallback(brk)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        barFeed.dispatchBars(10, 15, 8, 12, sessionClose=True)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getAvgFillPrice(), None)
        self.assertTrue(order.getExecutionInfo() is None)
        self.assertTrue(len(brk.getActiveOrders()) == 1)
        self.assertTrue(brk.getCash() == 5)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
        self.assertEqual(cb.eventCount, 2)

        # Fail to buy (couldn't get specific price). Canceled due to session close.
        cb = OrderUpdateCallback(brk)
        barFeed.dispatchBars(11, 15, 8, 12)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.assertTrue(order.isCanceled())
        self.assertEqual(order.getAvgFillPrice(), None)
        self.assertTrue(order.getExecutionInfo() is None)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 5)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
        self.assertTrue(cb.eventCount == 1)

    def testBuy_GTC(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(10, barFeed)

        order = brk.createLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 4, 2)
        order.setGoodTillCanceled(True)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 2)

        # Fail to buy (couldn't get specific price).
        cb = OrderUpdateCallback(brk)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        # Set sessionClose to true test that the order doesn't get canceled.
        barFeed.dispatchBars(10, 15, 8, 12, sessionClose=True)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 2)
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getAvgFillPrice(), None)
        self.assertTrue(order.getExecutionInfo() is None)
        self.assertTrue(len(brk.getActiveOrders()) == 1)
        self.assertTrue(brk.getCash() == 10)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
        self.assertEqual(cb.eventCount, 2)

        # Buy
        cb = OrderUpdateCallback(brk)
        barFeed.dispatchBars(2, 15, 1, 12)
        self.assertEqual(order.getFilled(), 2)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), 2)
        self.assertTrue(order.getExecutionInfo().getPrice() == 2)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 6)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 2)
        self.assertEqual(cb.eventCount, 1)


class StopOrderTestCase(BaseTestCase):
    def testStopHitWithoutVolume(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(1000, barFeed)

        # Buy. Stop >= 15.
        order = brk.createStopOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 15, 10)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())

        # 0 should get filled. There is not enough volume.
        barFeed.dispatchBars(18, 19, 17.01, 18, 3)
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 10)
        self.assertEqual(order.getStopHit(), True)
        self.assertEqual(order.getAvgFillPrice(), None)
        self.assertEqual(order.getExecutionInfo(), None)

    def testBuySellPartial_ActivateAndThenFill(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(1000, barFeed)

        # Buy. Stop >= 15.
        order = brk.createStopOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 15, 10)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())

        # 0 should get filled. The stop price should have not been hit.
        barFeed.dispatchBars(12, 14, 8, 12, 10)
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 10)
        self.assertEqual(order.getStopHit(), False)
        self.assertEqual(order.getAvgFillPrice(), None)
        self.assertEqual(order.getExecutionInfo(), None)
        # 0 should get filled. The stop price should have been hit but there is not enough volume.
        barFeed.dispatchBars(17.1, 18, 17.01, 18, 3)
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 10)
        self.assertEqual(order.getStopHit(), True)
        self.assertEqual(order.getAvgFillPrice(), None)
        self.assertEqual(order.getExecutionInfo(), None)
        # 5 should get filled.
        barFeed.dispatchBars(18, 18, 16, 18, 20)
        self.assertTrue(order.isPartiallyFilled())
        self.assertEqual(order.getFilled(), 5)
        self.assertEqual(order.getRemaining(), 5)
        self.assertEqual(order.getAvgFillPrice(), 18)
        self.assertEqual(order.getExecutionInfo().getPrice(), 18)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 5)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        # 5 should get filled.
        barFeed.dispatchBars(17.1, 18, 17.01, 18, 50)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 10)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getAvgFillPrice(), (18 + 17.1) / 2.0)
        self.assertEqual(order.getExecutionInfo().getPrice(), 17.1)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 5)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)

        # Sell. Stop <= 19.
        order = brk.createStopOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 19, 10)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        # 0 should get filled. The stop price should have not been hit.
        barFeed.dispatchBars(19.1, 19.5, 19.1, 19.4, 10)
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 10)
        self.assertEqual(order.getStopHit(), False)
        self.assertEqual(order.getAvgFillPrice(), None)
        self.assertEqual(order.getExecutionInfo(), None)
        # 0 should get filled. The stop price should have been hit but there is not enough volume.
        barFeed.dispatchBars(18, 18, 16, 18, 3)
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 10)
        self.assertEqual(order.getStopHit(), True)
        self.assertEqual(order.getAvgFillPrice(), None)
        self.assertEqual(order.getExecutionInfo(), None)
        # 5 should get filled.
        barFeed.dispatchBars(20, 21, 17, 18, 20)
        self.assertTrue(order.isPartiallyFilled())
        self.assertEqual(order.getFilled(), 5)
        self.assertEqual(order.getRemaining(), 5)
        self.assertEqual(order.getAvgFillPrice(), 20)
        self.assertEqual(order.getExecutionInfo().getPrice(), 20)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 5)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        # 2 should get filled.
        barFeed.dispatchBars(16, 21, 15, 18, 10)
        self.assertTrue(order.isPartiallyFilled())
        self.assertEqual(order.getFilled(), 7)
        self.assertEqual(order.getRemaining(), 3)
        self.assertEqual(order.getAvgFillPrice(), (20*5 + 16*2)/7.0)
        self.assertEqual(order.getExecutionInfo().getPrice(), 16)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 2)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        # 2 should get filled.
        barFeed.dispatchBars(21, 21, 17, 18, 10)
        self.assertTrue(order.isPartiallyFilled())
        self.assertEqual(order.getFilled(), 9)
        self.assertEqual(order.getRemaining(), 1)
        self.assertEqual(order.getAvgFillPrice(), (20*5 + 16*2 + 21*2)/9.0)
        self.assertEqual(order.getExecutionInfo().getPrice(), 21)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 2)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        # 1 should get filled.
        barFeed.dispatchBars(20, 21, 17, 18, 10)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 10)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getAvgFillPrice(), (20*5 + 16*2 + 21*2 + 20)/10.0)
        self.assertEqual(order.getExecutionInfo().getPrice(), 20)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 1)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)

    def testBuySellPartial_ActivateAndFill(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(1000, barFeed)

        # Buy. Stop >= 15.
        order = brk.createStopOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 15, 10)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())

        # 5 should get filled.
        barFeed.dispatchBars(18, 18, 16, 18, 20)
        self.assertEqual(order.getStopHit(), True)
        self.assertTrue(order.isPartiallyFilled())
        self.assertEqual(order.getFilled(), 5)
        self.assertEqual(order.getRemaining(), 5)
        self.assertEqual(order.getAvgFillPrice(), 18)
        self.assertEqual(order.getExecutionInfo().getPrice(), 18)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 5)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        # 0 should get filled. There is not enough volume.
        barFeed.dispatchBars(17.1, 18, 17.01, 18, 3)
        self.assertEqual(order.getAvgFillPrice(), 18)
        self.assertTrue(order.isPartiallyFilled())
        self.assertEqual(order.getFilled(), 5)
        self.assertEqual(order.getRemaining(), 5)
        # 5 should get filled.
        barFeed.dispatchBars(16, 18, 16, 18, 20)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 10)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getAvgFillPrice(), (18 + 16) / 2.0)
        self.assertEqual(order.getExecutionInfo().getPrice(), 16)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 5)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)

        # Sell. Stop <= 19.
        order = brk.createStopOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 19, 10)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        # 5 should get filled.
        barFeed.dispatchBars(20, 21, 17, 18, 20)
        self.assertEqual(order.getStopHit(), True)
        self.assertTrue(order.isPartiallyFilled())
        self.assertEqual(order.getFilled(), 5)
        self.assertEqual(order.getRemaining(), 5)
        self.assertEqual(order.getAvgFillPrice(), 19)
        self.assertEqual(order.getExecutionInfo().getPrice(), 19)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 5)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        # 0 should get filled. There is not enough volume.
        barFeed.dispatchBars(18, 18, 16, 18, 3)
        self.assertTrue(order.isPartiallyFilled())
        self.assertEqual(order.getAvgFillPrice(), 19)
        self.assertEqual(order.getFilled(), 5)
        self.assertEqual(order.getRemaining(), 5)
        # 2 should get filled.
        barFeed.dispatchBars(20, 21, 17, 18, 10)
        self.assertTrue(order.isPartiallyFilled())
        self.assertEqual(order.getFilled(), 7)
        self.assertEqual(order.getRemaining(), 3)
        self.assertEqual(order.getAvgFillPrice(), (19*5 + 20*2)/7.0)
        self.assertEqual(order.getExecutionInfo().getPrice(), 20)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 2)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        # 2 should get filled.
        barFeed.dispatchBars(21, 21, 17, 18, 10)
        self.assertTrue(order.isPartiallyFilled())
        self.assertEqual(order.getFilled(), 9)
        self.assertEqual(order.getRemaining(), 1)
        self.assertEqual(order.getAvgFillPrice(), (19*5 + 20*2 + 21*2)/9.0)
        self.assertEqual(order.getExecutionInfo().getPrice(), 21)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 2)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        # 1 should get filled.
        barFeed.dispatchBars(21, 21, 17, 18, 10)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 10)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getAvgFillPrice(), (19*5 + 20*2 + 21*3)/10.0)
        self.assertEqual(order.getExecutionInfo().getPrice(), 21)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 1)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)

    def testLongPosStopLoss(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(15, barFeed)

        # Buy
        cb = OrderUpdateCallback(brk)
        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        barFeed.dispatchBars(10, 15, 8, 12)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getAvgFillPrice(), 10)
        self.assertTrue(order.getExecutionInfo().getPrice() == 10)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 5)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
        self.assertEqual(cb.eventCount, 3)

        # Create stop loss order.
        cb = OrderUpdateCallback(brk)
        order = brk.createStopOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 9, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        barFeed.dispatchBars(10, 15, 10, 12)  # Stop loss not hit.
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.assertFalse(order.isFilled())
        self.assertTrue(len(brk.getActiveOrders()) == 1)
        self.assertTrue(brk.getCash() == 5)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
        self.assertEqual(cb.eventCount, 2)
        barFeed.dispatchBars(10, 15, 8, 12)  # Stop loss hit.
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), 9)
        self.assertTrue(order.getExecutionInfo().getPrice() == 9)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 5+9)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
        self.assertEqual(cb.eventCount, 3)

    def testLongPosStopLoss_GappingBars(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(15, barFeed)

        # Buy
        cb = OrderUpdateCallback(brk)
        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        barFeed.dispatchBars(10, 15, 8, 12)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getAvgFillPrice(), 10)
        self.assertTrue(order.getExecutionInfo().getPrice() == 10)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 5)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
        self.assertEqual(cb.eventCount, 3)

        # Create stop loss order.
        cb = OrderUpdateCallback(brk)
        order = brk.createStopOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 9, 1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        barFeed.dispatchBars(10, 15, 10, 12)  # Stop loss not hit.
        self.assertFalse(order.isFilled())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.assertTrue(len(brk.getActiveOrders()) == 1)
        self.assertTrue(brk.getCash() == 5)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
        self.assertEqual(cb.eventCount, 2)
        barFeed.dispatchBars(5, 8, 4, 7)  # Stop loss hit.
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getAvgFillPrice(), 5)
        self.assertTrue(order.getExecutionInfo().getPrice() == 5)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 5+5)  # Fill the stop loss order at open price.
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
        self.assertEqual(cb.eventCount, 3)

    def testShortPosStopLoss(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(15, barFeed)

        # Sell short
        cb = OrderUpdateCallback(brk)
        order = brk.createMarketOrder(broker.Order.Action.SELL_SHORT, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        barFeed.dispatchBars(10, 15, 8, 12)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getAvgFillPrice(), 10)
        self.assertTrue(order.getExecutionInfo().getPrice() == 10)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 15+10)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == -1)
        self.assertEqual(cb.eventCount, 3)

        # Create stop loss order.
        cb = OrderUpdateCallback(brk)
        order = brk.createStopOrder(broker.Order.Action.BUY_TO_COVER, BaseTestCase.TestInstrument, 11, 1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        barFeed.dispatchBars(8, 10, 7, 9)  # Stop loss not hit.
        self.assertFalse(order.isFilled())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.assertTrue(len(brk.getActiveOrders()) == 1)
        self.assertTrue(brk.getCash() == 15+10)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == -1)
        self.assertEqual(cb.eventCount, 2)
        barFeed.dispatchBars(10, 15, 8, 12)  # Stop loss hit.
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertTrue(order.getExecutionInfo().getPrice() == 11)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 15-1)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
        self.assertEqual(cb.eventCount, 3)

    def testShortPosStopLoss_GappingBars(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(15, barFeed)

        # Sell short
        cb = OrderUpdateCallback(brk)
        order = brk.createMarketOrder(broker.Order.Action.SELL_SHORT, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        barFeed.dispatchBars(10, 15, 8, 12)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getAvgFillPrice(), 10)
        self.assertTrue(order.getExecutionInfo().getPrice() == 10)
        self.assertTrue(order.getExecutionInfo().getCommission() == 0)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 15+10)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == -1)
        self.assertEqual(cb.eventCount, 3)

        # Create stop loss order.
        cb = OrderUpdateCallback(brk)
        order = brk.createStopOrder(broker.Order.Action.BUY_TO_COVER, BaseTestCase.TestInstrument, 11, 1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        barFeed.dispatchBars(8, 10, 7, 9)  # Stop loss not hit.
        self.assertFalse(order.isFilled())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.assertTrue(len(brk.getActiveOrders()) == 1)
        self.assertTrue(brk.getCash() == 15+10)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == -1)
        self.assertEqual(cb.eventCount, 2)
        barFeed.dispatchBars(15, 20, 13, 14)  # Stop loss hit.
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getAvgFillPrice(), 15)
        self.assertTrue(order.getExecutionInfo().getPrice() == 15)
        self.assertTrue(len(brk.getActiveOrders()) == 0)
        self.assertTrue(brk.getCash() == 15-5)
        self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
        self.assertEqual(cb.eventCount, 3)


class StopLimitOrderTestCase(BaseTestCase):
    def testStopHitWithoutVolume(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(1000, barFeed)

        # Buy. Stop >= 15. Buy <= 17.
        order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 15, 17, 10)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())

        # 0 should get filled. There is not enough volume.
        barFeed.dispatchBars(18, 19, 15, 18, 3)
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 10)
        self.assertEqual(order.getStopHit(), True)
        self.assertEqual(order.getAvgFillPrice(), None)
        self.assertEqual(order.getExecutionInfo(), None)

    def testRegressionBarGapsAboveStop(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(1000, barFeed)

        # Buy. Stop >= 15. Buy <= 17.
        order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 15, 17, 1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())

        # 1 should get filled at 17. Before the bug was fixed it was filled at 15.
        barFeed.dispatchBars(18, 18, 16, 18, 20)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getAvgFillPrice(), 17)
        self.assertEqual(order.getExecutionInfo().getPrice(), 17)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 1)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)

    def testBuySellPartial_ActivateAndThenFill(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(1000, barFeed)

        # Buy. Stop >= 15. Buy <= 17.
        order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 15, 17, 10)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())

        # 0 should get filled. The stop price should have not been hit.
        barFeed.dispatchBars(12, 14, 8, 12, 10)
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 10)
        self.assertEqual(order.getStopHit(), False)
        self.assertEqual(order.getAvgFillPrice(), None)
        self.assertEqual(order.getExecutionInfo(), None)
        # 0 should get filled. The stop price should have been hit.
        barFeed.dispatchBars(17.1, 18, 17.01, 18, 10)
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 10)
        self.assertEqual(order.getStopHit(), True)
        self.assertEqual(order.getAvgFillPrice(), None)
        self.assertEqual(order.getExecutionInfo(), None)
        # 5 should get filled.
        barFeed.dispatchBars(18, 18, 16, 18, 20)
        self.assertTrue(order.isPartiallyFilled())
        self.assertEqual(order.getFilled(), 5)
        self.assertEqual(order.getRemaining(), 5)
        self.assertEqual(order.getAvgFillPrice(), 17)
        self.assertEqual(order.getExecutionInfo().getPrice(), 17)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 5)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        # 0 should get filled.
        barFeed.dispatchBars(17.1, 18, 17.01, 18, 10)
        self.assertTrue(order.isPartiallyFilled())
        self.assertEqual(order.getFilled(), 5)
        self.assertEqual(order.getRemaining(), 5)
        self.assertEqual(order.getAvgFillPrice(), 17)
        self.assertEqual(order.getExecutionInfo().getPrice(), 17)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 5)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        # 5 should get filled.
        barFeed.dispatchBars(18, 18, 16, 18, 20)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 10)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getAvgFillPrice(), 17)
        self.assertEqual(order.getExecutionInfo().getPrice(), 17)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 5)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)

        # Sell. Stop <= 19. Sell >= 20.
        order = brk.createStopLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 19, 20, 10)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        # 0 should get filled. The stop price should have not been hit.
        barFeed.dispatchBars(19.1, 19.5, 19.1, 19.4, 10)
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 10)
        self.assertEqual(order.getStopHit(), False)
        self.assertEqual(order.getAvgFillPrice(), None)
        self.assertEqual(order.getExecutionInfo(), None)
        # 0 should get filled. The stop price should have been hit.
        barFeed.dispatchBars(18, 18, 16, 18, 20)
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 10)
        self.assertEqual(order.getStopHit(), True)
        self.assertEqual(order.getAvgFillPrice(), None)
        self.assertEqual(order.getExecutionInfo(), None)
        # 5 should get filled.
        barFeed.dispatchBars(20, 21, 17, 18, 20)
        self.assertTrue(order.isPartiallyFilled())
        self.assertEqual(order.getFilled(), 5)
        self.assertEqual(order.getRemaining(), 5)
        self.assertEqual(order.getAvgFillPrice(), 20)
        self.assertEqual(order.getExecutionInfo().getPrice(), 20)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 5)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        # 0 should get filled.
        barFeed.dispatchBars(18, 18, 16, 18, 20)
        self.assertTrue(order.isPartiallyFilled())
        self.assertEqual(order.getFilled(), 5)
        self.assertEqual(order.getRemaining(), 5)
        self.assertEqual(order.getAvgFillPrice(), 20)
        self.assertEqual(order.getExecutionInfo().getPrice(), 20)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 5)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        # 2 should get filled.
        barFeed.dispatchBars(20, 21, 17, 18, 10)
        self.assertTrue(order.isPartiallyFilled())
        self.assertEqual(order.getFilled(), 7)
        self.assertEqual(order.getRemaining(), 3)
        self.assertEqual(order.getAvgFillPrice(), 20)
        self.assertEqual(order.getExecutionInfo().getPrice(), 20)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 2)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        # 2 should get filled.
        barFeed.dispatchBars(21, 21, 17, 18, 10)
        self.assertTrue(order.isPartiallyFilled())
        self.assertEqual(order.getFilled(), 9)
        self.assertEqual(order.getRemaining(), 1)
        self.assertEqual(order.getAvgFillPrice(), (20*7 + 21*2) / 9.0)
        self.assertEqual(order.getExecutionInfo().getPrice(), 21)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 2)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        # 1 should get filled.
        barFeed.dispatchBars(21, 21, 17, 18, 10)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 10)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getAvgFillPrice(), (20*7 + 21*3) / 10.0)
        self.assertEqual(order.getExecutionInfo().getPrice(), 21)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 1)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)

    def testBuySellPartial_ActivateAndFill(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(1000, barFeed)

        # Buy. Stop >= 15. Buy <= 17.
        order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 15, 17, 10)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())

        # 5 should get filled.
        barFeed.dispatchBars(18, 18, 16, 18, 20)
        self.assertTrue(order.isPartiallyFilled())
        self.assertEqual(order.getFilled(), 5)
        self.assertEqual(order.getRemaining(), 5)
        self.assertEqual(order.getAvgFillPrice(), 17)
        self.assertEqual(order.getExecutionInfo().getPrice(), 17)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 5)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        # 0 should get filled.
        barFeed.dispatchBars(17.1, 18, 17.01, 18, 10)
        self.assertTrue(order.isPartiallyFilled())
        self.assertEqual(order.getFilled(), 5)
        self.assertEqual(order.getRemaining(), 5)
        self.assertEqual(order.getAvgFillPrice(), 17)
        self.assertEqual(order.getExecutionInfo().getPrice(), 17)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 5)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        # 5 should get filled.
        barFeed.dispatchBars(16, 18, 16, 18, 20)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 10)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getAvgFillPrice(), (17+16)/2.0)
        self.assertEqual(order.getExecutionInfo().getPrice(), 16)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 5)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)

        # Sell. Stop <= 19. Sell >= 20.
        order = brk.createStopLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 19, 20, 10)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        # 5 should get filled.
        barFeed.dispatchBars(20, 21, 17, 18, 20)
        self.assertTrue(order.isPartiallyFilled())
        self.assertEqual(order.getFilled(), 5)
        self.assertEqual(order.getRemaining(), 5)
        self.assertEqual(order.getAvgFillPrice(), 20)
        self.assertEqual(order.getExecutionInfo().getPrice(), 20)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 5)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        # 0 should get filled.
        barFeed.dispatchBars(18, 18, 16, 18, 20)
        self.assertTrue(order.isPartiallyFilled())
        self.assertEqual(order.getFilled(), 5)
        self.assertEqual(order.getRemaining(), 5)
        self.assertEqual(order.getAvgFillPrice(), 20)
        self.assertEqual(order.getExecutionInfo().getPrice(), 20)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 5)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        # 2 should get filled.
        barFeed.dispatchBars(20, 21, 17, 18, 10)
        self.assertTrue(order.isPartiallyFilled())
        self.assertEqual(order.getFilled(), 7)
        self.assertEqual(order.getRemaining(), 3)
        self.assertEqual(order.getAvgFillPrice(), 20)
        self.assertEqual(order.getExecutionInfo().getPrice(), 20)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 2)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        # 2 should get filled.
        barFeed.dispatchBars(21, 21, 17, 18, 10)
        self.assertTrue(order.isPartiallyFilled())
        self.assertEqual(order.getFilled(), 9)
        self.assertEqual(order.getRemaining(), 1)
        self.assertEqual(order.getAvgFillPrice(), (20*7 + 21*2) / 9.0)
        self.assertEqual(order.getExecutionInfo().getPrice(), 21)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 2)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        # 1 should get filled.
        barFeed.dispatchBars(21, 21, 17, 18, 10)
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 10)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getAvgFillPrice(), (20*7 + 21*3) / 10.0)
        self.assertEqual(order.getExecutionInfo().getPrice(), 21)
        self.assertEqual(order.getExecutionInfo().getQuantity(), 1)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)

    def testFillOpen(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(15, barFeed)

        # Buy. Stop >= 10. Buy <= 12.
        order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, stopPrice=10, limitPrice=12, quantity=1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price not hit. Limit price not hit.
        barFeed.dispatchBars(8, 9, 7, 8)
        self.assertFalse(order.getStopHit())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price not hit.
        barFeed.dispatchBars(13, 15, 13, 14)
        self.assertTrue(order.getStopHit())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Limit price hit (bars include the price). Fill at open price.
        barFeed.dispatchBars(11, 15, 10, 14)
        self.assertTrue(order.getStopHit())
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), 11)
        self.assertTrue(order.getExecutionInfo().getPrice() == 11)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

        # Sell. Stop <= 8. Sell >= 6.
        order = brk.createStopLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, stopPrice=8, limitPrice=6, quantity=1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price not hit. Limit price not hit.
        barFeed.dispatchBars(9, 10, 9, 10)
        self.assertFalse(order.getStopHit())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price not hit.
        barFeed.dispatchBars(4, 5, 3, 4)
        self.assertTrue(order.getStopHit())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Limit price hit (bars include the price). Fill at open price.
        barFeed.dispatchBars(7, 8, 6, 7)
        self.assertTrue(order.getStopHit())
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), 7)
        self.assertTrue(order.getExecutionInfo().getPrice() == 7)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

    def testFillOpen_GappingBars(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(15, barFeed)

        # Buy. Stop >= 10. Buy <= 12.
        order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, stopPrice=10, limitPrice=12, quantity=1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price not hit. Limit price not hit.
        barFeed.dispatchBars(8, 9, 7, 8)
        self.assertFalse(order.getStopHit())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price not hit.
        barFeed.dispatchBars(13, 18, 13, 17)
        self.assertTrue(order.getStopHit())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Limit price hit (bars don't include the price). Fill at open price.
        barFeed.dispatchBars(7, 9, 6, 8)
        self.assertTrue(order.getStopHit())
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), 7)
        self.assertTrue(order.getExecutionInfo().getPrice() == 7)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

        # Sell. Stop <= 8. Sell >= 6.
        order = brk.createStopLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, stopPrice=8, limitPrice=6, quantity=1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price not hit. Limit price not hit.
        barFeed.dispatchBars(9, 10, 9, 10)
        self.assertFalse(order.getStopHit())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price not hit.
        barFeed.dispatchBars(4, 5, 3, 4)
        self.assertTrue(order.getStopHit())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Limit price hit (bars don't include the price). Fill at open price.
        barFeed.dispatchBars(10, 12, 8, 10)
        self.assertTrue(order.getStopHit())
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), 10)
        self.assertTrue(order.getExecutionInfo().getPrice() == 10)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

    def testFillLimit(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(15, barFeed)

        # Buy. Stop >= 10. Buy <= 12.
        order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, stopPrice=10, limitPrice=12, quantity=1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price not hit. Limit price not hit.
        barFeed.dispatchBars(8, 9, 7, 8)
        self.assertFalse(order.getStopHit())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price not hit.
        barFeed.dispatchBars(13, 15, 13, 14)
        self.assertTrue(order.getStopHit())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Limit price hit. Fill at limit price.
        barFeed.dispatchBars(13, 15, 10, 14)
        self.assertTrue(order.getStopHit())
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), 12)
        self.assertTrue(order.getExecutionInfo().getPrice() == 12)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

        # Sell. Stop <= 8. Sell >= 6.
        order = brk.createStopLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, stopPrice=8, limitPrice=6, quantity=1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price not hit. Limit price not hit.
        barFeed.dispatchBars(9, 10, 9, 10)
        self.assertFalse(order.getStopHit())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price not hit.
        barFeed.dispatchBars(4, 5, 3, 4)
        self.assertTrue(order.getStopHit())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Limit price hit. Fill at limit price.
        barFeed.dispatchBars(5, 7, 5, 6)
        self.assertTrue(order.getStopHit())
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), 6)
        self.assertTrue(order.getExecutionInfo().getPrice() == 6)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

    def testHitStopAndLimit(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(15, barFeed)

        # Buy. Stop >= 10. Buy <= 12.
        order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, stopPrice=10, limitPrice=12, quantity=1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price hit. Fill at stop price.
        barFeed.dispatchBars(9, 15, 8, 14)
        self.assertTrue(order.getStopHit())
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), 10)
        self.assertTrue(order.getExecutionInfo().getPrice() == 10)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

        # Sell. Stop <= 8. Sell >= 6.
        order = brk.createStopLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, stopPrice=8, limitPrice=6, quantity=1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price hit. Fill at stop price.
        barFeed.dispatchBars(9, 10, 5, 8)
        self.assertTrue(order.getStopHit())
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), 8)
        self.assertTrue(order.getExecutionInfo().getPrice() == 8)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

    def testInvertedPrices_FillOpen(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(15, barFeed)

        # Buy. Stop >= 12. Buy <= 10.
        order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, stopPrice=12, limitPrice=10, quantity=1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price not hit. Limit price not hit.
        barFeed.dispatchBars(8, 9, 7, 8)
        self.assertFalse(order.getStopHit())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price not hit.
        barFeed.dispatchBars(11, 12, 10.5, 11)
        self.assertTrue(order.getStopHit())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Limit price hit. Fill at open price.
        barFeed.dispatchBars(9, 15, 8, 14)
        self.assertTrue(order.getStopHit())
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), 9)
        self.assertTrue(order.getExecutionInfo().getPrice() == 9)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

        # Sell. Stop <= 6. Sell >= 8.
        order = brk.createStopLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, stopPrice=6, limitPrice=8, quantity=1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price not hit. Limit price not hit.
        barFeed.dispatchBars(9, 10, 9, 10)
        self.assertFalse(order.getStopHit())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price not hit.
        barFeed.dispatchBars(7, 7, 6, 7)
        self.assertTrue(order.getStopHit())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Limit price hit. Fill at open price.
        barFeed.dispatchBars(9, 10, 8, 9)
        self.assertTrue(order.getStopHit())
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), 9)
        self.assertTrue(order.getExecutionInfo().getPrice() == 9)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

    def testInvertedPrices_FillOpen_GappingBars(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(15, barFeed)

        # Buy. Stop >= 12. Buy <= 10.
        order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, stopPrice=12, limitPrice=10, quantity=1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price not hit. Limit price not hit.
        barFeed.dispatchBars(8, 9, 7, 8)
        self.assertFalse(order.getStopHit())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price not hit.
        barFeed.dispatchBars(11, 12, 10.5, 11)
        self.assertTrue(order.getStopHit())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Limit price hit. Fill at open price.
        barFeed.dispatchBars(7, 9, 6, 8)
        self.assertTrue(order.getStopHit())
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), 7)
        self.assertTrue(order.getExecutionInfo().getPrice() == 7)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

        # Sell. Stop <= 6. Sell >= 8.
        order = brk.createStopLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, stopPrice=6, limitPrice=8, quantity=1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price not hit. Limit price not hit.
        barFeed.dispatchBars(9, 10, 9, 10)
        self.assertFalse(order.getStopHit())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price not hit.
        barFeed.dispatchBars(7, 7, 6, 7)
        self.assertTrue(order.getStopHit())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Limit price hit. Fill at open price.
        barFeed.dispatchBars(10, 10, 9, 9)
        self.assertTrue(order.getStopHit())
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), 10)
        self.assertTrue(order.getExecutionInfo().getPrice() == 10)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

    def testInvertedPrices_FillLimit(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(15, barFeed)

        # Buy. Stop >= 12. Buy <= 10.
        order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, stopPrice=12, limitPrice=10, quantity=1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price not hit. Limit price not hit.
        barFeed.dispatchBars(8, 9, 7, 8)
        self.assertFalse(order.getStopHit())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price not hit.
        barFeed.dispatchBars(11, 12, 10.5, 11)
        self.assertTrue(order.getStopHit())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Limit price hit. Fill at limit price.
        barFeed.dispatchBars(11, 13, 8, 9)
        self.assertTrue(order.getStopHit())
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), 10)
        self.assertTrue(order.getExecutionInfo().getPrice() == 10)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

        # Sell. Stop <= 6. Sell >= 8.
        order = brk.createStopLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, stopPrice=6, limitPrice=8, quantity=1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price not hit. Limit price not hit.
        barFeed.dispatchBars(9, 10, 9, 10)
        self.assertFalse(order.getStopHit())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price not hit.
        barFeed.dispatchBars(7, 7, 6, 7)
        self.assertTrue(order.getStopHit())
        self.assertTrue(order.isAccepted())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Limit price hit. Fill at limit price.
        barFeed.dispatchBars(7, 10, 6, 9)
        self.assertTrue(order.getStopHit())
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), 8)
        self.assertTrue(order.getExecutionInfo().getPrice() == 8)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

    def testInvertedPrices_HitStopAndLimit(self):
        barFeed = self.buildBarFeed(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        brk = self.buildBroker(15, barFeed)

        # Buy. Stop >= 12. Buy <= 10.
        order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, stopPrice=12, limitPrice=10, quantity=1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price hit. Fill at limit price.
        barFeed.dispatchBars(9, 15, 8, 14)
        self.assertTrue(order.getStopHit())
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), 10)
        self.assertTrue(order.getExecutionInfo().getPrice() == 10)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

        # Sell. Stop <= 6. Sell >= 8.
        order = brk.createStopLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, stopPrice=6, limitPrice=8, quantity=1)
        self.assertEqual(order.getSubmitDateTime(), None)
        brk.submitOrder(order)
        self.assertEqual(order.getSubmitDateTime(), barFeed.getCurrentDateTime())
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)

        # Stop price hit. Limit price hit. Fill at limit price.
        barFeed.dispatchBars(6, 10, 5, 7)
        self.assertTrue(order.getStopHit())
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getAvgFillPrice(), 8)
        self.assertTrue(order.getExecutionInfo().getPrice() == 8)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
