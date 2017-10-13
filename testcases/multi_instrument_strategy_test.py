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

from . import common

from pyalgotrade import bar
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.barfeed import sqlitefeed
from pyalgotrade import marketsession
from pyalgotrade import strategy
from pyalgotrade.technical import ma
from pyalgotrade.technical import cross


class NikkeiSpyStrategy(strategy.BacktestingStrategy):
    def __init__(self, feed, smaPeriod):
        strategy.BacktestingStrategy.__init__(self, feed)

        assert(smaPeriod > 3)
        self.__lead = "^n225"
        self.__lag = "spy"
        self.__adjClose = feed[self.__lead].getAdjCloseDataSeries()
        # Exit signal is more sensitive than entry.
        self.__fastSMA = ma.SMA(self.__adjClose, int(smaPeriod/2))
        self.__slowSMA = ma.SMA(self.__adjClose, smaPeriod)
        self.__pos = None

    def onEnterCanceled(self, position):
        assert(position == self.__pos)
        self.__pos = None

    def onExitOk(self, position):
        assert(position == self.__pos)
        self.__pos = None

    def __calculatePosSize(self):
        cash = self.getBroker().getCash()
        lastPrice = self.getFeed()[self.__lag][-1].getClose()
        ret = cash / lastPrice
        return int(ret)

    def onBars(self, bars):
        if bars.getBar(self.__lead):
            if cross.cross_above(self.__adjClose, self.__slowSMA) == 1 and self.__pos is None:
                shares = self.__calculatePosSize()
                if shares:
                    self.__pos = self.enterLong(self.__lag, shares)
            elif cross.cross_below(self.__adjClose, self.__fastSMA) == 1 and self.__pos is not None:
                self.__pos.exitMarket()


class TestCase(common.TestCase):
    def __testDifferentTimezonesImpl(self, feed):
        self.assertTrue("^n225" in feed)
        self.assertTrue("spy" in feed)
        self.assertTrue("cacho" not in feed)
        strat = NikkeiSpyStrategy(feed, 34)
        strat.run()
        self.assertEqual(round(strat.getResult(), 2), 1033854.48)

    def testDifferentTimezones(self):
        # Market times in UTC:
        # - TSE: 0hs ~ 6hs
        # - US: 14:30hs ~ 21hs
        feed = yahoofeed.Feed()
        for year in [2010, 2011]:
            feed.addBarsFromCSV("^n225", common.get_data_file_path("nikkei-%d-yahoofinance.csv" % year), marketsession.TSE.getTimezone())
            feed.addBarsFromCSV("spy", common.get_data_file_path("spy-%d-yahoofinance.csv" % year), marketsession.USEquities.getTimezone())

        self.__testDifferentTimezonesImpl(feed)

    def testDifferentTimezones_DBFeed(self):
        feed = sqlitefeed.Feed(common.get_data_file_path("multiinstrument.sqlite"), bar.Frequency.DAY)
        feed.loadBars("^n225")
        feed.loadBars("spy")
        self.__testDifferentTimezonesImpl(feed)

    def testDifferentTimezones_DBFeed_LocalizedBars(self):
        feed = sqlitefeed.Feed(common.get_data_file_path("multiinstrument.sqlite"), bar.Frequency.DAY)
        feed.loadBars("^n225", marketsession.TSE.getTimezone())
        feed.loadBars("spy", marketsession.USEquities.getTimezone())
        self.__testDifferentTimezonesImpl(feed)
