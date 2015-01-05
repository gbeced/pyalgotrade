# PyAlgoTrade
#
# Copyright 2011-2014 Gabriel Martin Becedillas Ruiz
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
import sys
import os
import matplotlib

# Force matplotlib to not use any Xwindows backend.
matplotlib.use('Agg')

from pyalgotrade.barfeed import yahoofeed
from pyalgotrade import plotter

import common

sys.path.append("samples")
import sma_crossover


class PlotterTestCase(unittest.TestCase):
    def testDownloadAndParseDaily(self):
        instrument = "orcl"
        barFeed = yahoofeed.Feed()
        barFeed.addBarsFromCSV(instrument, common.get_data_file_path("orcl-2000-yahoofinance.csv"))
        strat = sma_crossover.SMACrossOver(barFeed, instrument, 20)
        plt = plotter.StrategyPlotter(strat, True, True, True)
        plt.getInstrumentSubplot(instrument).addDataSeries("sma", strat.getSMA())
        strat.run()

        with common.TmpDir() as tmpPath:
            fig = plt.buildFigure()
            fig.set_size_inches(10, 8)
            png = os.path.join(tmpPath, "plotter_test.png")
            fig.savefig(png)
            self.assertEquals(open(common.get_data_file_path("plotter_test.png"), "r").read(), open(png, "r").read())
