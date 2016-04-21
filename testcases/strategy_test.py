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

import common

from pyalgotrade import strategy
from pyalgotrade import broker
from pyalgotrade.barfeed import yahoofeed


def get_by_datetime_or_date(dict_, dateTimeOrDate):
    ret = dict_.get(dateTimeOrDate, [])
    if len(ret) == 0 and isinstance(dateTimeOrDate, datetime.datetime):
        ret = dict_.get(dateTimeOrDate.date(), [])
    return ret


class TestStrategy(strategy.BacktestingStrategy):
    def __init__(self, barFeed, cash):
        strategy.BacktestingStrategy.__init__(self, barFeed, cash)

        # Maps dates to a tuple of (method, params)
        self.__orderEntry = {}

        self.__brokerOrdersGTC = False
        self.orderUpdatedCalls = 0
        self.onStartCalled = False
        self.onIdleCalled = False
        self.onFinishCalled = False

    def addOrder(self, dateTime, method, *args, **kwargs):
        self.__orderEntry.setdefault(dateTime, [])
        self.__orderEntry[dateTime].append((method, args, kwargs))

    def setBrokerOrdersGTC(self, gtc):
        self.__brokerOrdersGTC = gtc

    def onStart(self):
        self.onStartCalled = True

    def onIdle(self):
        self.onIdleCalled = True

    def onFinish(self, bars):
        self.onFinishCalled = True

    def onOrderUpdated(self, order):
        self.orderUpdatedCalls += 1

    def onBars(self, bars):
        dateTime = bars.getDateTime()

        # Check order entry.
        for meth, args, kwargs in get_by_datetime_or_date(self.__orderEntry, dateTime):
            order = meth(*args, **kwargs)
            order.setGoodTillCanceled(self.__brokerOrdersGTC)
            self.getBroker().submitOrder(order)


class StrategyTestCase(common.TestCase):
    TestInstrument = "doesntmatter"

    def loadDailyBarFeed(self):
        barFeed = yahoofeed.Feed()
        barFeed.addBarsFromCSV(StrategyTestCase.TestInstrument, common.get_data_file_path("orcl-2000-yahoofinance.csv"))
        return barFeed

    def createStrategy(self):
        barFeed = self.loadDailyBarFeed()
        strat = TestStrategy(barFeed, 1000)
        return strat


class BrokerOrderTestCase(StrategyTestCase):
    def testMarketOrder(self):
        strat = self.createStrategy()

        o = strat.getBroker().createMarketOrder(broker.Order.Action.BUY, StrategyTestCase.TestInstrument, 1)
        strat.getBroker().submitOrder(o)
        strat.run()
        self.assertTrue(o.isFilled())
        self.assertEqual(strat.orderUpdatedCalls, 2)


class StrategyOrderTestCase(StrategyTestCase):
    def testOrder(self):
        strat = self.createStrategy()

        o = strat.marketOrder(StrategyTestCase.TestInstrument, 1)
        strat.run()
        self.assertTrue(o.isFilled())
        self.assertEqual(strat.orderUpdatedCalls, 2)

    def testMarketOrderBuy(self):
        strat = self.createStrategy()

        o = strat.marketOrder(StrategyTestCase.TestInstrument, 1)
        strat.run()
        self.assertTrue(o.isFilled())
        self.assertEquals(o.getAction(), broker.Order.Action.BUY)
        self.assertEquals(o.getQuantity(), 1)
        self.assertEquals(o.getFilled(), 1)
        self.assertEquals(o.getRemaining(), 0)
        self.assertEqual(strat.orderUpdatedCalls, 2)

    def testMarketOrderSell(self):
        strat = self.createStrategy()

        o = strat.marketOrder(StrategyTestCase.TestInstrument, -2)
        strat.run()
        self.assertTrue(o.isFilled())
        self.assertEquals(o.getAction(), broker.Order.Action.SELL)
        self.assertEquals(o.getQuantity(), 2)
        self.assertEquals(o.getFilled(), 2)
        self.assertEquals(o.getRemaining(), 0)
        self.assertEqual(strat.orderUpdatedCalls, 2)

    def testLimitOrderBuy(self):
        strat = self.createStrategy()

        o = strat.limitOrder(StrategyTestCase.TestInstrument, 60, 1, True)
        strat.run()
        self.assertTrue(o.isFilled())
        self.assertEquals(o.getAction(), broker.Order.Action.BUY)
        self.assertEquals(o.getAvgFillPrice(), 56.13)
        self.assertEquals(o.getQuantity(), 1)
        self.assertEquals(o.getFilled(), 1)
        self.assertEquals(o.getRemaining(), 0)
        self.assertEqual(strat.orderUpdatedCalls, 2)

    def testLimitOrderSell(self):
        strat = self.createStrategy()

        o = strat.limitOrder(StrategyTestCase.TestInstrument, 60, -3, False)
        strat.run()
        self.assertTrue(o.isFilled())
        self.assertEquals(o.getAction(), broker.Order.Action.SELL)
        self.assertEquals(o.getAvgFillPrice(), 124.62)
        self.assertEquals(o.getQuantity(), 3)
        self.assertEquals(o.getFilled(), 3)
        self.assertEquals(o.getRemaining(), 0)
        self.assertEqual(strat.orderUpdatedCalls, 2)

    def testStopOrderBuy(self):
        strat = self.createStrategy()

        o = strat.stopOrder(StrategyTestCase.TestInstrument, 100, 1, False)
        strat.run()
        self.assertTrue(o.isFilled())
        self.assertEquals(o.getAction(), broker.Order.Action.BUY)
        self.assertEquals(o.getAvgFillPrice(), 124.62)
        self.assertEquals(o.getQuantity(), 1)
        self.assertEquals(o.getFilled(), 1)
        self.assertEquals(o.getRemaining(), 0)
        self.assertEqual(strat.orderUpdatedCalls, 2)

    def testStopOrderSell(self):
        strat = self.createStrategy()

        o = strat.stopOrder(StrategyTestCase.TestInstrument, 55, -2, True)
        strat.run()
        self.assertTrue(o.isFilled())
        self.assertEquals(o.getAction(), broker.Order.Action.SELL)
        self.assertEquals(o.getAvgFillPrice(), 55)
        self.assertEquals(o.getQuantity(), 2)
        self.assertEquals(o.getFilled(), 2)
        self.assertEquals(o.getRemaining(), 0)
        self.assertEqual(strat.orderUpdatedCalls, 2)
        self.assertEqual(o.getExecutionInfo().getDateTime(), datetime.datetime(2000, 1, 19))

    def testStopLimitOrderBuy(self):
        strat = self.createStrategy()

        o = strat.stopLimitOrder(StrategyTestCase.TestInstrument, 110, 100, 1, True)
        strat.run()
        self.assertTrue(o.isFilled())
        self.assertEquals(o.getAction(), broker.Order.Action.BUY)
        self.assertEquals(o.getAvgFillPrice(), 100)
        self.assertEquals(o.getQuantity(), 1)
        self.assertEquals(o.getFilled(), 1)
        self.assertEquals(o.getRemaining(), 0)
        self.assertEqual(strat.orderUpdatedCalls, 2)
        self.assertEqual(o.getExecutionInfo().getDateTime(), datetime.datetime(2000, 1, 5))

    def testStopLimitOrderSell(self):
        strat = self.createStrategy()

        o = strat.stopLimitOrder(StrategyTestCase.TestInstrument, 100, 110, -2, True)
        strat.run()
        self.assertTrue(o.isFilled())
        self.assertEquals(o.getAction(), broker.Order.Action.SELL)
        self.assertEquals(o.getAvgFillPrice(), 110)
        self.assertEquals(o.getQuantity(), 2)
        self.assertEquals(o.getFilled(), 2)
        self.assertEquals(o.getRemaining(), 0)
        self.assertEqual(strat.orderUpdatedCalls, 2)
        self.assertEqual(o.getExecutionInfo().getDateTime(), datetime.datetime(2000, 1, 10))


class OptionalOverridesTestCase(StrategyTestCase):
    def testOnStartIdleFinish(self):
        strat = self.createStrategy()
        strat.run()
        self.assertTrue(strat.onStartCalled)
        self.assertTrue(strat.onFinishCalled)
        self.assertFalse(strat.onIdleCalled)
