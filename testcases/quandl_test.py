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
import datetime

import common

from pyalgotrade.tools import quandl
from pyalgotrade import bar
from pyalgotrade.barfeed import quandlfeed


auth_token = None


class ToolsTestCase(common.TestCase):
    def testDownloadAndParseDaily(self):
        with common.TmpDir() as tmpPath:
            instrument = "ORCL"
            path = os.path.join(tmpPath, "quandl-daily-orcl-2010.csv")
            quandl.download_daily_bars("WIKI", instrument, 2010, path, auth_token)
            bf = quandlfeed.Feed()
            bf.addBarsFromCSV(instrument, path)
            bf.loadAll()
            self.assertEquals(bf[instrument][-1].getDateTime(), datetime.datetime(2010, 12, 31))
            self.assertEquals(bf[instrument][-1].getOpen(), 31.22)
            self.assertEquals(bf[instrument][-1].getHigh(), 31.33)
            self.assertEquals(bf[instrument][-1].getLow(), 30.93)
            self.assertEquals(bf[instrument][-1].getClose(), 31.3)
            self.assertEquals(bf[instrument][-1].getVolume(), 11716300)
            self.assertEquals(bf[instrument][-1].getPrice(), 31.3)
            # Not checking against a specific value since this is going to change
            # as time passes by.
            self.assertNotEquals(bf[instrument][-1].getAdjClose(), None)

    def testDownloadAndParseDaily_UseAdjClose(self):
        with common.TmpDir() as tmpPath:
            instrument = "ORCL"
            path = os.path.join(tmpPath, "quandl-daily-orcl-2010.csv")
            quandl.download_daily_bars("WIKI", instrument, 2010, path, auth_token)
            bf = quandlfeed.Feed()
            bf.addBarsFromCSV(instrument, path)
            # Need to setUseAdjustedValues(True) after loading the file because we
            # can't tell in advance if adjusted values are there or not.
            bf.setUseAdjustedValues(True)
            bf.loadAll()
            self.assertEquals(bf[instrument][-1].getDateTime(), datetime.datetime(2010, 12, 31))
            self.assertEquals(bf[instrument][-1].getOpen(), 31.22)
            self.assertEquals(bf[instrument][-1].getHigh(), 31.33)
            self.assertEquals(bf[instrument][-1].getLow(), 30.93)
            self.assertEquals(bf[instrument][-1].getClose(), 31.3)
            self.assertEquals(bf[instrument][-1].getVolume(), 11716300)
            self.assertEquals(bf[instrument][-1].getPrice(), bf[instrument][-1].getAdjClose())
            # Not checking against a specific value since this is going to change
            # as time passes by.
            self.assertNotEquals(bf[instrument][-1].getAdjClose(), None)

    def testDownloadAndParseDailyNoAdjClose(self):
        with common.TmpDir() as tmpPath:
            instrument = "ORCL"
            path = os.path.join(tmpPath, "quandl-daily-orcl-2013.csv")
            quandl.download_daily_bars("GOOG", "NASDAQ_ORCL", 2013, path, auth_token)
            bf = quandlfeed.Feed()
            bf.setNoAdjClose()
            bf.addBarsFromCSV(instrument, path)
            bf.loadAll()
            self.assertEquals(bf[instrument][-1].getDateTime(), datetime.datetime(2013, 12, 31))
            self.assertEquals(bf[instrument][-1].getOpen(), 37.94)
            self.assertEquals(bf[instrument][-1].getHigh(), 38.34)
            self.assertEquals(bf[instrument][-1].getLow(), 37.88)
            self.assertEquals(bf[instrument][-1].getClose(), 38.26)
            self.assertEquals(bf[instrument][-1].getVolume(), 11747517)
            self.assertEquals(bf[instrument][-1].getAdjClose(), None)
            self.assertEquals(bf[instrument][-1].getPrice(), 38.26)

    def testDownloadAndParseWeekly(self):
        with common.TmpDir() as tmpPath:
            instrument = "AAPL"
            path = os.path.join(tmpPath, "quandl-aapl-weekly-2010.csv")
            quandl.download_weekly_bars("WIKI", instrument, 2010, path, auth_token)
            bf = quandlfeed.Feed(frequency=bar.Frequency.WEEK)
            bf.addBarsFromCSV(instrument, path)
            bf.loadAll()
            # Quandl used to report 2010-1-3 as the first week of 2010.
            self.assertTrue(
                bf[instrument][0].getDateTime() in [datetime.datetime(2010, 1, 3), datetime.datetime(2010, 1, 10)]
            )
            self.assertEquals(bf[instrument][-1].getDateTime(), datetime.datetime(2010, 12, 26))
            self.assertEquals(bf[instrument][-1].getOpen(), 325.0)
            self.assertEquals(bf[instrument][-1].getHigh(), 325.15)
            self.assertEquals(bf[instrument][-1].getLow(), 323.17)
            self.assertEquals(bf[instrument][-1].getClose(), 323.6)
            self.assertEquals(bf[instrument][-1].getVolume(), 7969900)
            self.assertEquals(bf[instrument][-1].getPrice(), 323.6)
            # Not checking against a specific value since this is going to change
            # as time passes by.
            self.assertNotEquals(bf[instrument][-1].getAdjClose(), None)

    def testInvalidFrequency(self):
        with self.assertRaisesRegexp(Exception, "Invalid frequency.*"):
            quandlfeed.Feed(frequency=bar.Frequency.MINUTE)

    def testBuildFeedDaily(self):
        with common.TmpDir() as tmpPath:
            instrument = "ORCL"
            bf = quandl.build_feed("WIKI", [instrument], 2010, 2010, tmpPath, authToken=auth_token)
            bf.loadAll()
            self.assertEquals(bf[instrument][-1].getDateTime(), datetime.datetime(2010, 12, 31))
            self.assertEquals(bf[instrument][-1].getOpen(), 31.22)
            self.assertEquals(bf[instrument][-1].getHigh(), 31.33)
            self.assertEquals(bf[instrument][-1].getLow(), 30.93)
            self.assertEquals(bf[instrument][-1].getClose(), 31.3)
            self.assertEquals(bf[instrument][-1].getVolume(), 11716300)
            self.assertEquals(bf[instrument][-1].getPrice(), 31.3)
            # Not checking against a specific value since this is going to change
            # as time passes by.
            self.assertNotEquals(bf[instrument][-1].getAdjClose(), None)

    def testBuildFeedWeekly(self):
        with common.TmpDir() as tmpPath:
            instrument = "AAPL"
            bf = quandl.build_feed("WIKI", [instrument], 2010, 2010, tmpPath, bar.Frequency.WEEK, authToken=auth_token)
            bf.loadAll()
            # Quandl used to report 2010-1-3 as the first week of 2010.
            self.assertTrue(
                bf[instrument][0].getDateTime() in [datetime.datetime(2010, 1, 3), datetime.datetime(2010, 1, 10)]
            )
            self.assertEquals(bf[instrument][-1].getDateTime(), datetime.datetime(2010, 12, 26))
            self.assertEquals(bf[instrument][-1].getOpen(), 325.0)
            self.assertEquals(bf[instrument][-1].getHigh(), 325.15)
            self.assertEquals(bf[instrument][-1].getLow(), 323.17)
            self.assertEquals(bf[instrument][-1].getClose(), 323.6)
            self.assertEquals(bf[instrument][-1].getVolume(), 7969900)
            self.assertEquals(bf[instrument][-1].getPrice(), 323.6)
            # Not checking against a specific value since this is going to change
            # as time passes by.
            self.assertNotEquals(bf[instrument][-1].getAdjClose(), None)
