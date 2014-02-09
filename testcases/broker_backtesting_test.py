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

from pyalgotrade import broker
from pyalgotrade import bar
from pyalgotrade import barfeed
from pyalgotrade.broker import backtesting

import broker_common as common
from broker_common import BarsBuilder, BaseTestCase

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

class BacktestBrokerFactory(common.BrokerFactory):
    def getBroker(self, cash, barFeed, commission=None):
        return backtesting.Broker(cash, barFeed, commission)

    def getFixedCommissionPerTrade(self, amount):
        return backtesting.FixedPerTrade(amount)

class BacktestBrokerVisitor(common.BrokerVisitor):
    def onBars(self, broker, dateTime, bars):
        broker.onBars(dateTime, bars)

class BacktestBrokerTestCase():
    Factory = BacktestBrokerFactory()
    Visitor = BacktestBrokerVisitor()

class BrokerTestCase(BacktestBrokerTestCase, common.BrokerTestCase):
    pass

class MarketOrderTestCase(BacktestBrokerTestCase, common.MarketOrderTestCase):
    def testPortfolioValue(self):
        brk = self.Factory.getBroker(11, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Buy
        order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(10, 15, 8, 12))
        self.assertTrue(order.isFilled())
        self.assertEqual(len(brk.getActiveOrders()), 0)
        self.assertEqual(brk.getCash(), 1)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 1)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)

        self.assertEqual(brk.getEquityWithBars(barsBuilder.nextBars(11, 11, 11, 11)), 11 + 1)
        self.assertEqual(brk.getEquityWithBars(barsBuilder.nextBars(1, 1, 1, 1)),  1 + 1)

    def testSellShort_1(self):
        brk = self.Factory.getBroker(1000, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Short sell
        order = brk.createMarketOrder(broker.Order.Action.SELL_SHORT, BaseTestCase.TestInstrument, 1)
        brk.placeOrder(order)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(200, 200, 200, 200))
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(len(brk.getActiveOrders()), 0)
        self.assertEqual(brk.getCash(), 1200)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), -1)
        self.assertEqual(brk.getEquityWithBars(barsBuilder.nextBars(100, 100, 100, 100)), 1000 + 100)
        self.assertEqual(brk.getEquityWithBars(barsBuilder.nextBars(0, 0, 0, 0)), 1000 + 200)
        self.assertEqual(brk.getEquityWithBars(barsBuilder.nextBars(30, 30, 30, 30)), 1000 + 170)

        # Buy at the same price.
        order = brk.createMarketOrder(broker.Order.Action.BUY_TO_COVER, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.placeOrder(order)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(200, 200, 200, 200))
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(len(brk.getActiveOrders()), 0)
        self.assertEqual(brk.getCash(), 1000)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 0)

    def testSellShort_2(self):
        brk = self.Factory.getBroker(1000, barFeed=barfeed.BaseBarFeed(bar.Frequency.MINUTE))
        barsBuilder = BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)

        # Short sell 1
        order = brk.createMarketOrder(broker.Order.Action.SELL_SHORT, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.placeOrder(order)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(100, 100, 100, 100))
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        self.assertEqual(brk.getCash(), 1100)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), -1)
        self.assertEqual(brk.getEquityWithBars(barsBuilder.nextBars(100, 100, 100, 100)), 1000)
        self.assertEqual(brk.getEquityWithBars(barsBuilder.nextBars(0, 0, 0, 0)), 1000 + 100)
        self.assertEqual(brk.getEquityWithBars(barsBuilder.nextBars(70, 70, 70, 70)), 1000 + 30)
        self.assertEqual(brk.getEquityWithBars(barsBuilder.nextBars(200, 200, 200, 200)), 1000 - 100)

        # Buy 2 and earn 50
        order = brk.createMarketOrder(broker.Order.Action.BUY_TO_COVER, BaseTestCase.TestInstrument, 2)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 2)
        brk.placeOrder(order)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(50, 50, 50, 50))
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        self.assertEqual(order.getFilled(), 2)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 1)
        self.assertEqual(brk.getCash(), 1000)  # +50 from short sell operation, -50 from buy operation.
        self.assertEqual(brk.getEquityWithBars(barsBuilder.nextBars(50, 50, 50, 50)), 1000 + 50)
        self.assertEqual(brk.getEquityWithBars(barsBuilder.nextBars(70, 70, 70, 70)), 1000 + 50 + 20)

        # Sell 1 and earn 50
        order = brk.createMarketOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 1)
        self.assertEqual(order.getFilled(), 0)
        self.assertEqual(order.getRemaining(), 1)
        brk.placeOrder(order)
        self.Visitor.onBars(brk, *barsBuilder.nextTuple(100, 100, 100, 100))
        self.assertTrue(order.isFilled())
        self.assertEqual(order.getFilled(), 1)
        self.assertEqual(order.getRemaining(), 0)
        self.assertEqual(order.getExecutionInfo().getCommission(), 0)
        self.assertEqual(brk.getShares(BaseTestCase.TestInstrument), 0)
        self.assertEqual(brk.getEquityWithBars(barsBuilder.nextBars(70, 70, 70, 70)), 1000 + 50 + 50)

class LimitOrderTestCase(BacktestBrokerTestCase, common.LimitOrderTestCase):
    pass

class StopOrderTestCase(BacktestBrokerTestCase, common.StopOrderTestCase):
    pass

class StopLimitOrderTestCase(BacktestBrokerTestCase, common.StopLimitOrderTestCase):
    pass
