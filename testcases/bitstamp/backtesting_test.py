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

import pytest

from pyalgotrade import strategy
from pyalgotrade.bitstamp import broker
from pyalgotrade.bitcoincharts import barfeed as btcbarfeed

from testcases import common


SYMBOL = "BTC"
PRICE_CURRENCY = "USD"
INSTRUMENT = "BTC/USD"


def test_buy():

    class TestStrategy(strategy.BaseStrategy):
        def __init__(self, feed, brk):
            strategy.BaseStrategy.__init__(self, feed, brk)
            self.pos = None

        def onBars(self, bars):
            if not self.pos:
                self.pos = self.enterLongLimit(INSTRUMENT, 5.83, 5, True)

    barFeed = btcbarfeed.CSVTradeFeed()
    barFeed.addBarsFromCSV(common.get_data_file_path("bitstampUSD.csv"), instrument=INSTRUMENT)
    brk = broker.BacktestingBroker({PRICE_CURRENCY: 100}, barFeed)
    strat = TestStrategy(barFeed, brk)
    strat.run()

    assert strat.pos.getShares() == 5
    assert not strat.pos.entryActive()
    assert strat.pos.isOpen()
    assert strat.pos.getEntryOrder().getAvgFillPrice() == round((3 * 5.83 + 2 * 5.76) / 5.0, 2)


def test_order_fails_if_usd_amount_is_too_low():
    class TestStrategy(strategy.BaseStrategy):
        def __init__(self, feed, brk):
            strategy.BaseStrategy.__init__(self, feed, brk)
            self.pos = None

        def onBars(self, bars):
            if not self.pos:
                self.pos = self.enterLongLimit(INSTRUMENT, 4.99, 1, True)

    barFeed = btcbarfeed.CSVTradeFeed()
    barFeed.addBarsFromCSV(common.get_data_file_path("bitstampUSD.csv"), instrument=INSTRUMENT)
    brk = broker.BacktestingBroker({PRICE_CURRENCY: 100}, barFeed)
    strat = TestStrategy(barFeed, brk)

    with pytest.raises(Exception, match="USD amount must be >= 25"):
        strat.run()
