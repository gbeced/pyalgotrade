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

import sys
import logging

import common

from pyalgotrade.optimizer import local
from pyalgotrade import strategy
from pyalgotrade.barfeed import yahoofeed

sys.path.append("samples")
import sma_crossover


def parameters_generator(instrument, smaFirst, smaLast):
    for sma in range(smaFirst, smaLast+1):
        yield(instrument, sma)


class FailingStrategy(strategy.BacktestingStrategy):
    def __init__(self, barFeed, instrument, smaPeriod):
        super(FailingStrategy, self).__init__(barFeed)

    def onBars(self, bars):
        raise Exception("oh no!")


class OptimizerTestCase(common.TestCase):
    def testLocal(self):
        barFeed = yahoofeed.Feed()
        instrument = "orcl"
        barFeed.addBarsFromCSV(instrument, common.get_data_file_path("orcl-2000-yahoofinance.csv"))
        res = local.run(
            sma_crossover.SMACrossOver, barFeed, parameters_generator(instrument, 5, 100), logLevel=logging.DEBUG
        )
        self.assertEquals(round(res.getResult(), 2), 1295462.6)
        self.assertEquals(res.getParameters()[1], 20)

    def testFailingStrategy(self):
        barFeed = yahoofeed.Feed()
        instrument = "orcl"
        barFeed.addBarsFromCSV(instrument, common.get_data_file_path("orcl-2000-yahoofinance.csv"))
        res = local.run(FailingStrategy, barFeed, parameters_generator(instrument, 5, 100), logLevel=logging.DEBUG)
        self.assertIsNone(res)
