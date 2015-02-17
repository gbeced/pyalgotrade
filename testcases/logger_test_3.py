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

from pyalgotrade import strategy
from pyalgotrade.broker import backtesting
from pyalgotrade import bar
from pyalgotrade import logger
from pyalgotrade.barfeed import membf


class TestBarFeed(membf.BarFeed):
    def barsHaveAdjClose(self):
        raise NotImplementedError()


class Strategy(strategy.BaseStrategy):
    def __init__(self, barFeed, cash):
        strategy.BaseStrategy.__init__(self, barFeed, backtesting.Broker(cash, barFeed))

    def onBars(self, bars):
        self.info("bla")
        logger.getLogger("custom").info("ble")


def main():
    bf = TestBarFeed(bar.Frequency.DAY)
    bars = [
        bar.BasicBar(datetime.datetime(2000, 1, 1), 10, 10, 10, 10, 10, 10, bar.Frequency.DAY),
        ]
    bf.addBarsFromSequence("orcl", bars)

    strat = Strategy(bf, 1000)
    strat.run()
