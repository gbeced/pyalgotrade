# PyAlgoTrade
#
# Copyright 2011-2018 Gabriel Martin Becedillas Ruiz
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

from testcases.bitstamp.bitstamp_test import TestStrategy, TestingLiveTradeFeed, TestingLiveBroker, SYMBOL, \
    PRICE_CURRENCY, INSTRUMENT


def test_map_user_transactions_to_order_events():

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

    assert len(strat.orderExecutionInfo) == 2
    assert strat.orderExecutionInfo[0].getPrice() == 578.79
    assert strat.orderExecutionInfo[0].getQuantity() == 0.04557395
    assert strat.orderExecutionInfo[0].getCommission() == 0.14
    assert strat.orderExecutionInfo[0].getDateTime().date() == datetime.datetime.now().date()
    assert strat.orderExecutionInfo[1].getPrice() == 567.21
    assert strat.orderExecutionInfo[1].getQuantity() == 0.04601436
    assert strat.orderExecutionInfo[1].getCommission() == 0.14
    assert strat.orderExecutionInfo[1].getDateTime().date() == datetime.datetime.now().date()


def test_cancel_order():

    class Strategy(TestStrategy):
        def __init__(self, feed, brk):
            super(Strategy, self).__init__(feed, brk)

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

    assert brk.getBalance(SYMBOL) == 0
    assert brk.getBalance(PRICE_CURRENCY) == 0
    assert len(strat.orderExecutionInfo) == 1
    assert strat.orderExecutionInfo[0] is None
    assert len(strat.ordersUpdated) == 1
    assert strat.ordersUpdated[0].isCanceled()


def test_buy_and_sell():

    class Strategy(TestStrategy):
        def __init__(self, feed, brk):
            super(Strategy, self).__init__(feed, brk)
            self.buyOrder = None
            self.sellOrder = None

        def onOrderUpdated(self, orderEvent):
            super(Strategy, self).onOrderUpdated(orderEvent)
            order = orderEvent.getOrder()

            if order == self.buyOrder and order.isPartiallyFilled():
                if self.sellOrder is None:
                    self.sellOrder = self.limitOrder(INSTRUMENT, 10, -0.5)
                    brk.getHTTPClient().addUserTransaction(self.sellOrder.getId(), -0.5, 5, 10, 0.01)
            elif order == self.sellOrder and order.isFilled():
                self.stop()

        def onBars(self, bars):
            if self.buyOrder is None:
                self.buyOrder = self.limitOrder(INSTRUMENT, 10, 1)
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

    assert strat.buyOrder.isPartiallyFilled()
    assert strat.sellOrder.isFilled()
    # 2 events for each order: 1 for accepted, 1 for fill.
    assert len(strat.orderExecutionInfo) == 4
    assert strat.orderExecutionInfo[0] is None
    assert strat.orderExecutionInfo[1].getPrice() == 10
    assert strat.orderExecutionInfo[1].getQuantity() == 0.5
    assert strat.orderExecutionInfo[1].getCommission() == 0.01
    assert strat.orderExecutionInfo[1].getDateTime().date() == datetime.datetime.now().date()
    assert strat.orderExecutionInfo[2] is None
    assert strat.orderExecutionInfo[3].getPrice() == 10
    assert strat.orderExecutionInfo[3].getQuantity() == 0.5
    assert strat.orderExecutionInfo[3].getCommission() == 0.01
    assert strat.orderExecutionInfo[3].getDateTime().date() == datetime.datetime.now().date()
