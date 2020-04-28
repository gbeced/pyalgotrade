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
import logging

from pyalgotrade import strategy
from pyalgotrade import bar
from pyalgotrade import logger
from pyalgotrade.barfeed import membf


PRICE_CURRENCY = "USD"
INSTRUMENT = "orcl/%s" % PRICE_CURRENCY


class TestBarFeed(membf.BarFeed):
    def barsHaveAdjClose(self):
        raise NotImplementedError()


class BacktestingStrategy(strategy.BacktestingStrategy):
    def __init__(self, barFeed, cash):
        super(BacktestingStrategy, self).__init__(barFeed, balances={PRICE_CURRENCY: cash})

    def onBars(self, bars):
        self.info("bla")
        self.marketOrder(INSTRUMENT, 1)


def main():
    bf = TestBarFeed(bar.Frequency.DAY)
    bars = [
        bar.BasicBar(
            INSTRUMENT, datetime.datetime(2000, 1, 1), 10, 10, 10, 10, 10, 10, bar.Frequency.DAY
        ),
        bar.BasicBar(
            INSTRUMENT, datetime.datetime(2000, 1, 2), 10, 10, 10, 10, 10, 10, bar.Frequency.DAY
        ),
        ]
    bf.addBarsFromSequence(INSTRUMENT, bars)

    logger.getLogger().setLevel(logging.DEBUG)
    strat = BacktestingStrategy(bf, 1)
    strat.run()
