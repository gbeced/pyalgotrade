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
import os

import common

from pyalgotrade.barfeed import ninjatraderfeed
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.barfeed import csvfeed
from pyalgotrade.tools import resample
from pyalgotrade import marketsession
from pyalgotrade.utils import dt
from pyalgotrade.dataseries import resampled as resampled_ds
from pyalgotrade.barfeed import resampled as resampled_bf
from pyalgotrade.dataseries import bards
from pyalgotrade import bar
from pyalgotrade import dispatcher
from pyalgotrade import resamplebase


class IntraDayRange(common.TestCase):
    def __testMinuteRangeImpl(self, timezone=None):
        freq = bar.Frequency.MINUTE

        begin = datetime.datetime(2011, 1, 1, 1, 1)
        end = datetime.datetime(2011, 1, 1, 1, 2)
        if timezone is not None:
            begin = dt.localize(begin, timezone)
            end = dt.localize(end, timezone)

        r = resamplebase.build_range(begin + datetime.timedelta(seconds=5), freq)
        self.assertEqual(r.getBeginning(), begin)
        for i in range(freq):
            self.assertTrue(r.belongs(begin + datetime.timedelta(seconds=i)))
        self.assertFalse(r.belongs(begin + datetime.timedelta(seconds=freq+1)))
        self.assertEqual(r.getEnding(), end)

    def __testFiveMinuteRangeImpl(self, timezone=None):
        freq = 60*5

        begin = datetime.datetime(2011, 1, 1, 1)
        end = datetime.datetime(2011, 1, 1, 1, 5)
        if timezone is not None:
            begin = dt.localize(begin, timezone)
            end = dt.localize(end, timezone)

        r = resamplebase.build_range(begin + datetime.timedelta(seconds=120), freq)
        self.assertEqual(r.getBeginning(), begin)
        for i in range(freq):
            self.assertTrue(r.belongs(begin + datetime.timedelta(seconds=i)))
        self.assertFalse(r.belongs(begin + datetime.timedelta(seconds=freq+1)))
        self.assertEqual(r.getEnding(), end)

    def __testHourRangeImpl(self, timezone=None):
        freq = bar.Frequency.HOUR

        begin = datetime.datetime(2011, 1, 1, 16)
        end = datetime.datetime(2011, 1, 1, 17)
        if timezone is not None:
            begin = dt.localize(begin, timezone)
            end = dt.localize(end, timezone)

        r = resamplebase.build_range(begin + datetime.timedelta(seconds=120), freq)
        self.assertEqual(r.getBeginning(), begin)
        for i in range(freq):
            self.assertTrue(r.belongs(begin + datetime.timedelta(seconds=i)))
        self.assertFalse(r.belongs(begin + datetime.timedelta(seconds=freq+1)))
        self.assertEqual(r.getEnding(), end)

    def testMinuteRange(self):
        self.__testMinuteRangeImpl()

    def testMinuteRangeLocalized(self):
        self.__testMinuteRangeImpl(marketsession.NASDAQ.timezone)

    def testFiveMinuteRange(self):
        self.__testFiveMinuteRangeImpl()

    def testFiveMinuteRangeLocalized(self):
        self.__testFiveMinuteRangeImpl(marketsession.NASDAQ.timezone)

    def testHourRange(self):
        self.__testHourRangeImpl()

    def testHourRangeLocalized(self):
        self.__testHourRangeImpl(marketsession.NASDAQ.timezone)


class DayRange(common.TestCase):
    def __testImpl(self, timezone=None):
        freq = bar.Frequency.DAY

        begin = datetime.datetime(2011, 1, 1)
        end = datetime.datetime(2011, 1, 2)
        if timezone is not None:
            begin = dt.localize(begin, timezone)
            end = dt.localize(end, timezone)

        r = resamplebase.build_range(begin + datetime.timedelta(hours=5, minutes=25), freq)
        self.assertEqual(r.getBeginning(), begin)
        for i in range(freq):
            self.assertTrue(r.belongs(begin + datetime.timedelta(seconds=i)))
        self.assertFalse(r.belongs(begin + datetime.timedelta(seconds=freq+1)))
        self.assertEqual(r.getEnding(), end)

    def testOk(self):
        self.__testImpl()

    def testLocalizedOk(self):
        self.__testImpl(marketsession.NASDAQ.timezone)


class MonthRange(common.TestCase):
    def test31Days(self):
        freq = bar.Frequency.MONTH
        begin = datetime.datetime(2011, 1, 1)
        r = resamplebase.build_range(begin + datetime.timedelta(hours=5, minutes=25), freq)
        self.assertEqual(r.getBeginning(), begin)
        for i in range(freq):
            self.assertTrue(r.belongs(begin + datetime.timedelta(seconds=i)))
        self.assertFalse(r.belongs(begin + datetime.timedelta(seconds=freq+1)))
        self.assertEqual(r.getEnding(), datetime.datetime(2011, 2, 1))

    def test28Days(self):
        freq = bar.Frequency.MONTH
        begin = datetime.datetime(2011, 2, 1)
        r = resamplebase.build_range(begin + datetime.timedelta(hours=5, minutes=25), freq)
        self.assertEqual(r.getBeginning(), begin)
        for i in range(freq - bar.Frequency.DAY*3):
            self.assertTrue(r.belongs(begin + datetime.timedelta(seconds=i)))
        self.assertFalse(r.belongs(begin + datetime.timedelta(seconds=freq+1)))
        self.assertEqual(r.getEnding(), datetime.datetime(2011, 3, 1))

    def testDecember(self):
        freq = bar.Frequency.MONTH
        begin = datetime.datetime(2011, 12, 1)
        r = resamplebase.build_range(begin + datetime.timedelta(hours=5, minutes=25), freq)
        self.assertEqual(r.getBeginning(), begin)
        for i in range(freq):
            self.assertTrue(r.belongs(begin + datetime.timedelta(seconds=i)))
        self.assertFalse(r.belongs(begin + datetime.timedelta(seconds=freq+1)))
        self.assertEqual(r.getEnding(), datetime.datetime(2012, 1, 1))


class DataSeriesTestCase(common.TestCase):

    def testResample(self):
        barDs = bards.BarDataSeries()
        resampledDS = resampled_ds.ResampledDataSeries(barDs.getCloseDataSeries(), bar.Frequency.MINUTE, sum)
        resampledBarDS = resampled_ds.ResampledBarDataSeries(barDs, bar.Frequency.MINUTE)

        barDs.append(bar.BasicBar(datetime.datetime(2011, 1, 1, 1, 1, 1), 2.1, 3, 1, 2, 10, 1, bar.Frequency.SECOND))
        barDs.append(bar.BasicBar(datetime.datetime(2011, 1, 1, 1, 1, 2), 2, 3, 1, 2.3, 10, 2, bar.Frequency.SECOND))
        barDs.append(bar.BasicBar(datetime.datetime(2011, 1, 1, 1, 2, 1), 2, 3, 1, 2, 10, 2, bar.Frequency.SECOND))

        self.assertEqual(len(resampledBarDS), 1)
        self.assertEqual(resampledBarDS[0].getDateTime(), datetime.datetime(2011, 1, 1, 1, 1))
        self.assertEqual(resampledBarDS[0].getOpen(), 2.1)
        self.assertEqual(resampledBarDS[0].getHigh(), 3)
        self.assertEqual(resampledBarDS[0].getLow(), 1)
        self.assertEqual(resampledBarDS[0].getClose(), 2.3)
        self.assertEqual(resampledBarDS[0].getVolume(), 20)
        self.assertEqual(resampledBarDS[0].getAdjClose(), 2)
        self.assertEqual(resampledDS[-1], 2 + 2.3)

        resampledBarDS.pushLast()
        self.assertEqual(len(resampledBarDS), 2)
        self.assertEqual(resampledBarDS[1].getDateTime(), datetime.datetime(2011, 1, 1, 1, 2))
        self.assertEqual(resampledBarDS[1].getOpen(), 2)
        self.assertEqual(resampledBarDS[1].getHigh(), 3)
        self.assertEqual(resampledBarDS[1].getLow(), 1)
        self.assertEqual(resampledBarDS[1].getClose(), 2)
        self.assertEqual(resampledBarDS[1].getVolume(), 10)
        self.assertEqual(resampledBarDS[1].getAdjClose(), 2)

        resampledDS.pushLast()
        self.assertEqual(resampledDS[1], 2)

    def testResampleNinjaTraderHour(self):
        with common.TmpDir() as tmp_path:
            # Resample.
            feed = ninjatraderfeed.Feed(ninjatraderfeed.Frequency.MINUTE)
            feed.addBarsFromCSV("spy", common.get_data_file_path("nt-spy-minute-2011.csv"))
            resampledBarDS = resampled_ds.ResampledBarDataSeries(feed["spy"], bar.Frequency.HOUR)
            resampledFile = os.path.join(tmp_path, "hour-nt-spy-minute-2011.csv")
            resample.resample_to_csv(feed, bar.Frequency.HOUR, resampledFile)
            resampledBarDS.pushLast()  # Need to manually push the last stot since time didn't change.

            # Load the resampled file.
            feed = csvfeed.GenericBarFeed(bar.Frequency.HOUR, marketsession.USEquities.getTimezone())
            feed.addBarsFromCSV("spy", resampledFile)
            feed.loadAll()

        self.assertEqual(len(feed["spy"]), 340)
        self.assertEqual(feed["spy"][0].getDateTime(), dt.localize(datetime.datetime(2011, 1, 3, 9), marketsession.USEquities.getTimezone()))
        self.assertEqual(feed["spy"][-1].getDateTime(), dt.localize(datetime.datetime(2011, 2, 1, 1), marketsession.USEquities.getTimezone()))
        self.assertEqual(feed["spy"][0].getOpen(), 126.35)
        self.assertEqual(feed["spy"][0].getHigh(), 126.45)
        self.assertEqual(feed["spy"][0].getLow(), 126.3)
        self.assertEqual(feed["spy"][0].getClose(), 126.4)
        self.assertEqual(feed["spy"][0].getVolume(), 3397.0)
        self.assertEqual(feed["spy"][0].getAdjClose(), None)

        self.assertEqual(len(resampledBarDS), len(feed["spy"]))
        self.assertEqual(resampledBarDS[0].getDateTime(), dt.as_utc(datetime.datetime(2011, 1, 3, 9)))
        self.assertEqual(resampledBarDS[-1].getDateTime(), dt.as_utc(datetime.datetime(2011, 2, 1, 1)))

    def testResampleNinjaTraderDay(self):
        with common.TmpDir() as tmp_path:
            # Resample.
            feed = ninjatraderfeed.Feed(ninjatraderfeed.Frequency.MINUTE)
            feed.addBarsFromCSV("spy", common.get_data_file_path("nt-spy-minute-2011.csv"))
            resampledBarDS = resampled_ds.ResampledBarDataSeries(feed["spy"], bar.Frequency.DAY)
            resampledFile = os.path.join(tmp_path, "day-nt-spy-minute-2011.csv")
            resample.resample_to_csv(feed, bar.Frequency.DAY, resampledFile)
            resampledBarDS.pushLast()  # Need to manually push the last stot since time didn't change.

            # Load the resampled file.
            feed = csvfeed.GenericBarFeed(bar.Frequency.DAY)
            feed.addBarsFromCSV("spy", resampledFile, marketsession.USEquities.getTimezone())
            feed.loadAll()

        self.assertEqual(len(feed["spy"]), 25)
        self.assertEqual(feed["spy"][0].getDateTime(), dt.localize(datetime.datetime(2011, 1, 3), marketsession.USEquities.getTimezone()))
        self.assertEqual(feed["spy"][-1].getDateTime(), dt.localize(datetime.datetime(2011, 2, 1), marketsession.USEquities.getTimezone()))

        self.assertEqual(len(resampledBarDS), len(feed["spy"]))
        self.assertEqual(resampledBarDS[0].getDateTime(), dt.as_utc(datetime.datetime(2011, 1, 3)))
        self.assertEqual(resampledBarDS[-1].getDateTime(), dt.as_utc(datetime.datetime(2011, 2, 1)))

    def testCheckNow(self):
        barDs = bards.BarDataSeries()
        resampledBarDS = resampled_ds.ResampledBarDataSeries(barDs, bar.Frequency.MINUTE)

        barDateTime = datetime.datetime(2014, 07, 07, 22, 46, 28, 10000)
        barDs.append(bar.BasicBar(barDateTime, 2.1, 3, 1, 2, 10, 1, bar.Frequency.MINUTE))
        self.assertEqual(len(resampledBarDS), 0)

        resampledBarDS.checkNow(barDateTime + datetime.timedelta(minutes=1))
        self.assertEqual(len(resampledBarDS), 1)
        self.assertEqual(barDs[0].getOpen(), resampledBarDS[0].getOpen())
        self.assertEqual(barDs[0].getHigh(), resampledBarDS[0].getHigh())
        self.assertEqual(barDs[0].getLow(), resampledBarDS[0].getLow())
        self.assertEqual(barDs[0].getClose(), resampledBarDS[0].getClose())
        self.assertEqual(barDs[0].getVolume(), resampledBarDS[0].getVolume())
        self.assertEqual(barDs[0].getAdjClose(), resampledBarDS[0].getAdjClose())
        self.assertEqual(resampledBarDS[0].getDateTime(), datetime.datetime(2014, 07, 07, 22, 46))


class BarFeedTestCase(common.TestCase):

    def testResampledBarFeed(self):
        barFeed = yahoofeed.Feed()
        barFeed.addBarsFromCSV("spy", common.get_data_file_path("spy-2010-yahoofinance.csv"))
        barFeed.addBarsFromCSV("nikkei", common.get_data_file_path("nikkei-2010-yahoofinance.csv"))
        resampledBarFeed = resampled_bf.ResampledBarFeed(barFeed, bar.Frequency.MONTH)

        disp = dispatcher.Dispatcher()
        disp.addSubject(barFeed)
        disp.addSubject(resampledBarFeed)
        disp.run()

        weeklySpyBarDS = resampledBarFeed["spy"]
        weeklyNikkeiBarDS = resampledBarFeed["nikkei"]

        # Check first bar
        self.assertEqual(weeklySpyBarDS[0].getDateTime().date(), datetime.date(2010, 1, 1))
        self.assertEqual(weeklyNikkeiBarDS[0].getDateTime().date(), datetime.date(2010, 1, 1))

        # Check last bar
        self.assertEqual(weeklySpyBarDS[-1].getDateTime().date(), datetime.date(2010, 11, 1))
        self.assertEqual(weeklyNikkeiBarDS[-1].getDateTime().date(), datetime.date(2010, 11, 1))
