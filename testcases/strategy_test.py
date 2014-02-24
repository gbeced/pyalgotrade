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

from pyalgotrade import strategy
from pyalgotrade import broker
from pyalgotrade.barfeed import yahoofeed
import common


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
            self.getBroker().placeOrder(order)


class StrategyTestCase(unittest.TestCase):
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
        strat.getBroker().placeOrder(o)
        strat.run()
        self.assertTrue(o.isFilled())
        self.assertEqual(strat.orderUpdatedCalls, 2)


class StrategyOrderTestCase(StrategyTestCase):
    def testMarketOrder(self):
        strat = self.createStrategy()

        o = strat.order(StrategyTestCase.TestInstrument, 1)
        strat.run()
        self.assertTrue(o.isFilled())
        self.assertEqual(strat.orderUpdatedCalls, 2)


class OptionalOverridesTestCase(StrategyTestCase):
    def testOnStartIdleFinish(self):
        strat = self.createStrategy()
        strat.run()
        self.assertTrue(strat.onStartCalled)
        self.assertTrue(strat.onFinishCalled)
        self.assertFalse(strat.onIdleCalled)
