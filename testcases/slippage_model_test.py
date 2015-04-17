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

import broker_backtesting_test

from pyalgotrade import broker
from pyalgotrade.broker import slippage
from pyalgotrade.broker import backtesting
from pyalgotrade import bar


class BaseTestCase(unittest.TestCase):
    TestInstrument = "orcl"


class NoSlippageTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.slippage = slippage.NoSlippage()
        self.barsBuilder = broker_backtesting_test.BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.DAY)

    def __test_impl(self, action):
        order = backtesting.MarketOrder(
            action, BaseTestCase.TestInstrument, 5, False, broker.IntegerTraits()
        )
        price = 10

        slippedPrice = self.slippage.calculatePrice(
            order, price, order.getQuantity(), self.barsBuilder.nextBar(10, 11, 9, 10, volume=100), 0
        )
        self.assertEqual(price, slippedPrice)

        slippedPrice = self.slippage.calculatePrice(
            order, price, order.getQuantity(), self.barsBuilder.nextBar(10, 11, 9, 10, volume=100), 20
        )
        self.assertEqual(slippedPrice, price)

    def test_buy_market_order(self):
        self.__test_impl(broker.Order.Action.BUY)

    def test_sell_market_order(self):
        self.__test_impl(broker.Order.Action.SELL)


class VolumeShareSlippageTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.priceImpact = 0.1
        self.slippage = slippage.VolumeShareSlippage(self.priceImpact)
        self.barsBuilder = broker_backtesting_test.BarsBuilder(BaseTestCase.TestInstrument, bar.Frequency.DAY)

    def __test_impl(self, action):
        order = backtesting.MarketOrder(
            action, BaseTestCase.TestInstrument, 25, False, broker.IntegerTraits()
        )
        price = 10
        volumeUsed = 0

        # Try the order once.
        slippedPrice = self.slippage.calculatePrice(
            order, price, order.getQuantity(), self.barsBuilder.nextBar(10, 11, 9, 10, volume=100), volumeUsed
        )
        quantity = order.getQuantity()
        expectedPriceImpactPct = quantity/100.0 * quantity/100.0 * self.priceImpact
        self.assertEqual(expectedPriceImpactPct, 0.00625)
        if action == broker.Order.Action.BUY:
            self.assertEqual(slippedPrice, price * (1 + expectedPriceImpactPct))
        else:
            self.assertEqual(slippedPrice, price * (1 - expectedPriceImpactPct))

        # Try the same order once again.
        volumeUsed += quantity
        quantity += order.getQuantity()

        slippedPrice = self.slippage.calculatePrice(
            order, price, order.getQuantity(), self.barsBuilder.nextBar(10, 11, 9, 10, volume=100), volumeUsed
        )
        expectedPriceImpactPct = quantity/100.0 * quantity/100.0 * self.priceImpact
        self.assertEqual(expectedPriceImpactPct, 0.025)
        if action == broker.Order.Action.BUY:
            self.assertEqual(slippedPrice, price * (1 + expectedPriceImpactPct))
        else:
            self.assertEqual(slippedPrice, price * (1 - expectedPriceImpactPct))

    def test_buy_market_order(self):
        self.__test_impl(broker.Order.Action.BUY)

    def test_sell_market_order(self):
        self.__test_impl(broker.Order.Action.SELL)

    def test_full_volume_used(self):
        orderSize = 100
        order = backtesting.MarketOrder(
            broker.Order.Action.BUY, BaseTestCase.TestInstrument, orderSize, False, broker.IntegerTraits()
        )
        price = 10
        volumeUsed = 0

        # Try the order once.
        slippedPrice = self.slippage.calculatePrice(
            order,
            price,
            order.getQuantity(),
            self.barsBuilder.nextBar(10, 11, 9, 10, volume=orderSize),
            volumeUsed
        )
        self.assertEqual(slippedPrice, price*1.1)
