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

import os

import common

from pyalgotrade.tools import yahoofinance
from pyalgotrade import bar
from pyalgotrade.barfeed import yahoofeed


class ToolsTestCase(common.TestCase):
    def testDownloadAndParseDaily(self):
        instrument = "orcl"

        with common.TmpDir() as tmp_path:
            path = os.path.join(tmp_path, "orcl-2010.csv")
            yahoofinance.download_daily_bars(instrument, 2010, path)
            bf = yahoofeed.Feed()
            bf.addBarsFromCSV(instrument, path)
            bf.loadAll()
            self.assertEqual(round(bf[instrument][-1].getOpen(), 2), 31.22)
            self.assertEqual(round(bf[instrument][-1].getClose(), 2), 31.30)

    def testDownloadAndParseWeekly(self):
        instrument = "aapl"

        with common.TmpDir() as tmp_path:
            path = os.path.join(tmp_path, "aapl-weekly-2013.csv")
            yahoofinance.download_weekly_bars(instrument, 2013, path)
            bf = yahoofeed.Feed(frequency=bar.Frequency.WEEK)
            bf.addBarsFromCSV(instrument, path)
            bf.loadAll()
            self.assertEqual(round(bf[instrument][-1].getOpen(), 2), 557.46)
            self.assertEqual(round(bf[instrument][-1].getHigh(), 2), 561.28)
            self.assertEqual(round(bf[instrument][-1].getLow(), 2), 540.43)
            self.assertEqual(round(bf[instrument][-1].getClose(), 2), 540.98)
            self.assertTrue(bf[instrument][-1].getVolume() in (9852500, 9855900, 68991600))

    def testBuildDailyFeed(self):
        with common.TmpDir() as tmpPath:
            instrument = "orcl"
            bf = yahoofinance.build_feed([instrument], 2010, 2010, storage=tmpPath)
            bf.loadAll()
            self.assertEqual(round(bf[instrument][-1].getOpen(), 2), 31.22)
            self.assertEqual(round(bf[instrument][-1].getClose(), 2), 31.30)

    def testBuildWeeklyFeed(self):
        with common.TmpDir() as tmpPath:
            instrument = "aapl"
            bf = yahoofinance.build_feed([instrument], 2013, 2013, storage=tmpPath, frequency=bar.Frequency.WEEK)
            bf.loadAll()
            self.assertEqual(round(bf[instrument][-1].getOpen(), 2), 557.46)
            self.assertEqual(round(bf[instrument][-1].getHigh(), 2), 561.28)
            self.assertEqual(round(bf[instrument][-1].getLow(), 2), 540.43)
            self.assertEqual(round(bf[instrument][-1].getClose(), 2), 540.98)
            self.assertTrue(bf[instrument][-1].getVolume() in (9852500, 9855900, 68991600))

    def testInvalidDates(self):
        instrument = "orcl"

        # Don't skip errors.
        with self.assertRaisesRegexp(Exception, "404 Client Error: Not Found"):
            with common.TmpDir() as tmpPath:
                bf = yahoofinance.build_feed([instrument], 2100, 2101, storage=tmpPath, frequency=bar.Frequency.DAY)

        # Skip errors.
        with common.TmpDir() as tmpPath:
            bf = yahoofinance.build_feed(
                [instrument], 2100, 2101, storage=tmpPath, frequency=bar.Frequency.DAY, skipErrors=True
            )
            bf.loadAll()
            self.assertNotIn(instrument, bf)
