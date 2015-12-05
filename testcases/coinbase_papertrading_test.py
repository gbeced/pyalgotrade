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

import test_strategy
from pyalgotrade.coinbase import client
from pyalgotrade.coinbase import livefeed
from pyalgotrade.coinbase import broker
from pyalgotrade.coinbase import common


class PaperTradingTestCase(unittest.TestCase):
    def testBuyAndSell(self):

        class Strategy(test_strategy.BaseTestStrategy):
            def __init__(self, barFeed, broker):
                super(Strategy, self).__init__(barFeed, broker)
                self.pos = None

            def onBars(self, bars):
                if self.pos is None:
                    self.pos = self.enterLong(common.btc_symbol, 0.1, goodTillCanceled=True)
                elif self.pos.isOpen():
                    if self.pos.entryFilled() and not self.pos.exitActive():
                        self.pos.exitMarket(goodTillCanceled=True)
                else:
                    self.stop()

        coinbaseCli = client.Client()
        barFeed = livefeed.LiveTradeFeed(coinbaseCli)
        brk = broker.BacktestingBroker(1000, barFeed)
        strat = Strategy(barFeed, brk)
        strat.run()
        self.assertTrue(len(strat.posExecutionInfo) > 0)
        self.assertTrue(len(strat.ordersUpdated) > 0)
        self.assertTrue(len(strat.orderExecutionInfo) > 0)
