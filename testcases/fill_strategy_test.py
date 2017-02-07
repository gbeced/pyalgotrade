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

import unittest
import datetime

import broker_backtesting_test

from pyalgotrade import broker
from pyalgotrade.broker import fillstrategy
from pyalgotrade.broker import backtesting
from pyalgotrade import bar


class BaseTestCase(unittest.TestCase):
    TestInstrument = "orcl"


class FreeFunctionsTestCase(BaseTestCase):
    def testStopOrderTriggerBuy(self):
        barsBuilder = broker_backtesting_test.BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        # Bar is below
        self.assertEqual(fillstrategy.get_stop_price_trigger(broker.Order.Action.BUY, 10, False, barsBuilder.nextBar(5, 5, 5, 5)), None)
        self.assertEqual(fillstrategy.get_stop_price_trigger(broker.Order.Action.BUY, 10, False, barsBuilder.nextBar(5, 6, 4, 5)), None)
        # High touches
        self.assertEqual(fillstrategy.get_stop_price_trigger(broker.Order.Action.BUY, 10, False, barsBuilder.nextBar(5, 10, 4, 9)), 10)
        # High penetrates
        self.assertEqual(fillstrategy.get_stop_price_trigger(broker.Order.Action.BUY, 10, False, barsBuilder.nextBar(5, 11, 4, 9)), 10)
        # Open touches
        self.assertEqual(fillstrategy.get_stop_price_trigger(broker.Order.Action.BUY, 10, False, barsBuilder.nextBar(10, 10, 10, 10)), 10)
        # Open is above
        self.assertEqual(fillstrategy.get_stop_price_trigger(broker.Order.Action.BUY, 10, False, barsBuilder.nextBar(11, 12, 4, 9)), 11)
        # Bar gaps above
        self.assertEqual(fillstrategy.get_stop_price_trigger(broker.Order.Action.BUY, 10, False, barsBuilder.nextBar(12, 13, 11, 12)), 12)

    def testStopOrderTriggerSell(self):
        barsBuilder = broker_backtesting_test.BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        # Bar is above
        self.assertEqual(fillstrategy.get_stop_price_trigger(broker.Order.Action.SELL, 10, False, barsBuilder.nextBar(15, 15, 15, 15)), None)
        self.assertEqual(fillstrategy.get_stop_price_trigger(broker.Order.Action.SELL, 10, False, barsBuilder.nextBar(15, 16, 11, 15)), None)
        # Low touches
        self.assertEqual(fillstrategy.get_stop_price_trigger(broker.Order.Action.SELL, 10, False, barsBuilder.nextBar(15, 16, 10, 11)), 10)
        # Low penetrates
        self.assertEqual(fillstrategy.get_stop_price_trigger(broker.Order.Action.SELL, 10, False, barsBuilder.nextBar(15, 16, 9, 11)), 10)
        # Open touches
        self.assertEqual(fillstrategy.get_stop_price_trigger(broker.Order.Action.SELL, 10, False, barsBuilder.nextBar(10, 10, 10, 10)), 10)
        # Open is below
        self.assertEqual(fillstrategy.get_stop_price_trigger(broker.Order.Action.SELL, 10, False, barsBuilder.nextBar(9, 12, 4, 9)), 9)
        # Bar gaps below
        self.assertEqual(fillstrategy.get_stop_price_trigger(broker.Order.Action.SELL, 10, False, barsBuilder.nextBar(8, 9, 6, 9)), 8)

    def testLimitOrderTriggerBuy(self):
        barsBuilder = broker_backtesting_test.BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        # Bar is above
        self.assertEqual(fillstrategy.get_limit_price_trigger(broker.Order.Action.BUY, 10, False, barsBuilder.nextBar(15, 15, 15, 15)), None)
        self.assertEqual(fillstrategy.get_limit_price_trigger(broker.Order.Action.BUY, 10, False, barsBuilder.nextBar(15, 16, 11, 15)), None)
        # Low touches
        self.assertEqual(fillstrategy.get_limit_price_trigger(broker.Order.Action.BUY, 10, False, barsBuilder.nextBar(15, 16, 10, 11)), 10)
        # Low penetrates
        self.assertEqual(fillstrategy.get_limit_price_trigger(broker.Order.Action.BUY, 10, False, barsBuilder.nextBar(15, 16, 9, 11)), 10)
        # Open touches
        self.assertEqual(fillstrategy.get_limit_price_trigger(broker.Order.Action.BUY, 10, False, barsBuilder.nextBar(10, 10, 10, 10)), 10)
        # Open is below
        self.assertEqual(fillstrategy.get_limit_price_trigger(broker.Order.Action.BUY, 10, False, barsBuilder.nextBar(9, 12, 4, 9)), 9)
        # Bar gaps below
        self.assertEqual(fillstrategy.get_limit_price_trigger(broker.Order.Action.BUY, 10, False, barsBuilder.nextBar(8, 9, 6, 9)), 8)

    def testLimitOrderTriggerSell(self):
        barsBuilder = broker_backtesting_test.BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        # Bar is below
        self.assertEqual(fillstrategy.get_limit_price_trigger(broker.Order.Action.SELL, 10, False, barsBuilder.nextBar(5, 5, 5, 5)), None)
        self.assertEqual(fillstrategy.get_limit_price_trigger(broker.Order.Action.SELL, 10, False, barsBuilder.nextBar(5, 6, 4, 5)), None)
        # High touches
        self.assertEqual(fillstrategy.get_limit_price_trigger(broker.Order.Action.SELL, 10, False, barsBuilder.nextBar(5, 10, 4, 9)), 10)
        # High penetrates
        self.assertEqual(fillstrategy.get_limit_price_trigger(broker.Order.Action.SELL, 10, False, barsBuilder.nextBar(5, 11, 4, 9)), 10)
        # Open touches
        self.assertEqual(fillstrategy.get_limit_price_trigger(broker.Order.Action.SELL, 10, False, barsBuilder.nextBar(10, 10, 10, 10)), 10)
        # Open is above
        self.assertEqual(fillstrategy.get_limit_price_trigger(broker.Order.Action.SELL, 10, False, barsBuilder.nextBar(11, 12, 4, 9)), 11)
        # Bar gaps above
        self.assertEqual(fillstrategy.get_limit_price_trigger(broker.Order.Action.SELL, 10, False, barsBuilder.nextBar(12, 13, 11, 12)), 12)


class DefaultStrategyTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.barsBuilder = broker_backtesting_test.BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.MINUTE)
        self.strategy = fillstrategy.DefaultStrategy()

    def __getFilledMarketOrder(self, quantity, price):
        order = backtesting.MarketOrder(
            broker.Order.Action.BUY,
            BaseTestCase.TestInstrument,
            quantity,
            False,
            broker.IntegerTraits()
        )
        order.setState(broker.Order.State.ACCEPTED)
        order.addExecutionInfo(broker.OrderExecutionInfo(price, quantity, 0, datetime.datetime.now()))
        return order

    def testVolumeLimitPerBar(self):
        volume = 100
        self.strategy.onBars(None, self.barsBuilder.nextBars(11, 12, 4, 9, volume))
        self.assertEquals(self.strategy.getVolumeLeft()[BaseTestCase.TestInstrument], 25)
        self.assertEquals(self.strategy.getVolumeUsed()[BaseTestCase.TestInstrument], 0)

        self.strategy.onOrderFilled(None, self.__getFilledMarketOrder(24, 11))
        self.assertEquals(self.strategy.getVolumeLeft()[BaseTestCase.TestInstrument], 1)
        self.assertEquals(self.strategy.getVolumeUsed()[BaseTestCase.TestInstrument], 24)

        with self.assertRaisesRegexp(Exception, "Invalid fill quantity 25. Not enough volume left 1"):
            self.strategy.onOrderFilled(None, self.__getFilledMarketOrder(25, 11))
        self.assertEquals(self.strategy.getVolumeLeft()[BaseTestCase.TestInstrument], 1)
        self.assertEquals(self.strategy.getVolumeUsed()[BaseTestCase.TestInstrument], 24)
