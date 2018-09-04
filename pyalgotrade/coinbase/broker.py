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

from pyalgotrade import broker
from pyalgotrade.broker import backtesting
from pyalgotrade.coinbase import common


class Commission(backtesting.Commission):
    def calculate(self, order, price, quantity):
        ret = 0
        # We're assuming that limit orders never get filled immediately.
        if order.getType() == broker.Order.Type.MARKET:
            ret = 0.0025
        return ret


class BacktestingBroker(backtesting.Broker):
    """
    A Coinbase backtesting broker.

    :param cash: The initial amount of cash.
    :type cash: int/float.
    :param barFeed: The bar feed that will provide the bars.
    :type barFeed: :class:`pyalgotrade.barfeed.BarFeed`

    .. note::
        * Only market and limit orders are supported.
        * Orders are automatically set as **goodTillCanceled=True** and  **allOrNone=False**.
        * BUY_TO_COVER orders are mapped to BUY orders.
        * SELL_SHORT orders are mapped to SELL orders.
    """

    def __init__(self, cash, barFeed):
        backtesting.Broker.__init__(self, cash, barFeed)
        self.setCommission(Commission())

    def getInstrumentTraits(self, instrument):
        return common.BTCTraits()

    def createStopOrder(self, action, instrument, stopPrice, quantity):
        raise Exception("Stop orders are not supported")

    def createStopLimitOrder(self, action, instrument, stopPrice, limitPrice, quantity):
        raise Exception("Stop limit orders are not supported")

