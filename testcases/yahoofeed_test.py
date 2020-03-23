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

from . import common
from . import barfeed_test
from . import feed_test

from pyalgotrade.utils import dt
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.barfeed import csvfeed
from pyalgotrade import bar
from pyalgotrade import marketsession


INSTRUMENT = "ORCL"
PRICE_CURRENCY = "USD"


class BarFeedEventHandler_TestLoadOrder:
    def __init__(self, testcase, barFeed, instrument, priceCurrency):
        self.__testcase = testcase
        self.__count = 0
        self.__prevDateTime = None
        self.__barFeed = barFeed
        self.__instrument = instrument
        self.__priceCurrency = priceCurrency

    def onBars(self, dateTime, bars):
        self.__count += 1
        dateTime = bars.getBar(self.__instrument, self.__priceCurrency).getDateTime()
        if self.__prevDateTime is not None:
            # Check that bars are loaded in order
            self.__testcase.assertTrue(self.__prevDateTime < dateTime)
            ds = self.__barFeed.getDataSeries(self.__instrument, self.__priceCurrency)
            # Check that the last value in the dataseries match the current datetime.
            self.__testcase.assertEqual(ds[-1].getDateTime(), dateTime)
            # Check that the datetime for the last value matches that last datetime in the dataseries.
            self.__testcase.assertEqual(ds[-1].getDateTime(), ds.getDateTimes()[-1])
        self.__prevDateTime = dateTime

    def getEventCount(self):
        return self.__count


class BarFeedEventHandler_TestFilterRange:
    def __init__(self, testcase, instrument, priceCurrency, fromDate, toDate):
        self.__testcase = testcase
        self.__count = 0
        self.__instrument = instrument
        self.__priceCurrency = priceCurrency
        self.__fromDate = fromDate
        self.__toDate = toDate

    def onBars(self, dateTime, bars):
        self.__count += 1

        if self.__fromDate is not None:
            self.__testcase.assertTrue(
                bars.getBar(self.__instrument, self.__priceCurrency).getDateTime() >= self.__fromDate
            )
        if self.__toDate is not None:
            self.__testcase.assertTrue(
                bars.getBar(self.__instrument, self.__priceCurrency).getDateTime() <= self.__toDate
            )

    def getEventCount(self):
        return self.__count


class FeedTestCase(common.TestCase):
    def __parseDate(self, date):
        parser = yahoofeed.RowParser(INSTRUMENT, PRICE_CURRENCY, datetime.time(23, 59), bar.Frequency.DAY)
        row = {
            "Date": date,
            "Close": 0,
            "Open": 0,
            "High": 0,
            "Low": 0,
            "Volume": 0,
            "Adj Close": 0}
        return parser.parseBar(row).getDateTime()

    def testInvalidConstruction(self):
        with self.assertRaises(Exception):
            yahoofeed.Feed(maxLen=0)

    def testDuplicateBars(self):
        barFeed = yahoofeed.Feed()
        barFeed.addBarsFromCSV(INSTRUMENT, PRICE_CURRENCY, common.get_data_file_path("orcl-2000-yahoofinance.csv"))
        barFeed.addBarsFromCSV(INSTRUMENT, PRICE_CURRENCY, common.get_data_file_path("orcl-2000-yahoofinance.csv"))
        with self.assertRaisesRegexp(Exception, "Duplicate bars found for.*"):
            barFeed.loadAll()

    def testBaseBarFeed(self):
        barFeed = yahoofeed.Feed()
        barFeed.sanitizeBars(True)
        barFeed.addBarsFromCSV(INSTRUMENT, PRICE_CURRENCY, common.get_data_file_path("orcl-2000-yahoofinance.csv"))
        barfeed_test.check_base_barfeed(self, barFeed, True)

    def testInvalidFrequency(self):
        with self.assertRaisesRegexp(Exception, "Invalid frequency.*"):
            yahoofeed.Feed(frequency=bar.Frequency.MINUTE)

    def testBaseFeedInterface(self):
        barFeed = yahoofeed.Feed()
        barFeed.addBarsFromCSV(INSTRUMENT, PRICE_CURRENCY, common.get_data_file_path("orcl-2000-yahoofinance.csv"))
        feed_test.tstBaseFeedInterface(self, barFeed)

    def testParseDate_1(self):
        date = self.__parseDate("1950-01-01")
        self.assertTrue(date.day == 1)
        self.assertTrue(date.month == 1)
        self.assertTrue(date.year == 1950)

    def testParseDate_2(self):
        date = self.__parseDate("2000-01-01")
        self.assertTrue(date.day == 1)
        self.assertTrue(date.month == 1)
        self.assertTrue(date.year == 2000)

    def testDateCompare(self):
        self.assertTrue(self.__parseDate("2000-01-01") == self.__parseDate("2000-01-01"))
        self.assertTrue(self.__parseDate("2000-01-01") != self.__parseDate("2001-01-01"))
        self.assertTrue(self.__parseDate("1999-01-01") < self.__parseDate("2001-01-01"))
        self.assertTrue(self.__parseDate("2011-01-01") > self.__parseDate("2001-02-02"))

    def testCSVFeedLoadOrder(self):
        barFeed = yahoofeed.Feed()
        barFeed.addBarsFromCSV(INSTRUMENT, PRICE_CURRENCY, common.get_data_file_path("orcl-2000-yahoofinance.csv"))
        barFeed.addBarsFromCSV(INSTRUMENT, PRICE_CURRENCY, common.get_data_file_path("orcl-2001-yahoofinance.csv"))

        # Dispatch and handle events.
        handler = BarFeedEventHandler_TestLoadOrder(self, barFeed, INSTRUMENT, PRICE_CURRENCY)
        barFeed.getNewValuesEvent().subscribe(handler.onBars)
        while not barFeed.eof():
            barFeed.dispatch()
        self.assertTrue(handler.getEventCount() > 0)

    def __testFilteredRangeImpl(self, fromDate, toDate):
        barFeed = yahoofeed.Feed()
        barFeed.setBarFilter(csvfeed.DateRangeFilter(fromDate, toDate))
        barFeed.addBarsFromCSV(INSTRUMENT, PRICE_CURRENCY, common.get_data_file_path("orcl-2000-yahoofinance.csv"))
        barFeed.addBarsFromCSV(INSTRUMENT, PRICE_CURRENCY, common.get_data_file_path("orcl-2001-yahoofinance.csv"))

        # Dispatch and handle events.
        handler = BarFeedEventHandler_TestFilterRange(self, INSTRUMENT, PRICE_CURRENCY, fromDate, toDate)
        barFeed.getNewValuesEvent().subscribe(handler.onBars)
        while not barFeed.eof():
            barFeed.dispatch()
        self.assertTrue(handler.getEventCount() > 0)

    def testFilteredRangeFrom(self):
        # Only load bars from year 2001.
        self.__testFilteredRangeImpl(datetime.datetime(2001, 1, 1, 00, 00), None)

    def testFilteredRangeTo(self):
        # Only load bars up to year 2000.
        self.__testFilteredRangeImpl(None, datetime.datetime(2000, 12, 31, 23, 55))

    def testFilteredRangeFromTo(self):
        # Only load bars in year 2000.
        self.__testFilteredRangeImpl(datetime.datetime(2000, 1, 1, 00, 00), datetime.datetime(2000, 12, 31, 23, 55))

    def testWithoutTimezone(self):
        barFeed = yahoofeed.Feed()
        barFeed.addBarsFromCSV(INSTRUMENT, PRICE_CURRENCY, common.get_data_file_path("orcl-2000-yahoofinance.csv"))
        barFeed.addBarsFromCSV(INSTRUMENT, PRICE_CURRENCY, common.get_data_file_path("orcl-2001-yahoofinance.csv"))
        for dateTime, bars in barFeed:
            bar = bars.getBar(INSTRUMENT, PRICE_CURRENCY)
            self.assertTrue(dt.datetime_is_naive(bar.getDateTime()))

    def testWithDefaultTimezone(self):
        barFeed = yahoofeed.Feed(timezone=marketsession.USEquities.getTimezone())
        barFeed.addBarsFromCSV(INSTRUMENT, PRICE_CURRENCY, common.get_data_file_path("orcl-2000-yahoofinance.csv"))
        barFeed.addBarsFromCSV(INSTRUMENT, PRICE_CURRENCY, common.get_data_file_path("orcl-2001-yahoofinance.csv"))
        for dateTime, bars in barFeed:
            bar = bars.getBar(INSTRUMENT, PRICE_CURRENCY)
            self.assertFalse(dt.datetime_is_naive(bar.getDateTime()))

    def testWithPerFileTimezone(self):
        barFeed = yahoofeed.Feed()
        barFeed.addBarsFromCSV(
            INSTRUMENT, PRICE_CURRENCY, common.get_data_file_path("orcl-2000-yahoofinance.csv"),
            marketsession.USEquities.getTimezone()
        )
        barFeed.addBarsFromCSV(
            INSTRUMENT, PRICE_CURRENCY, common.get_data_file_path("orcl-2001-yahoofinance.csv"),
            marketsession.USEquities.getTimezone()
        )
        for dateTime, bars in barFeed:
            bar = bars.getBar(INSTRUMENT, PRICE_CURRENCY)
            self.assertFalse(dt.datetime_is_naive(bar.getDateTime()))

    def testWithIntegerTimezone(self):
        try:
            barFeed = yahoofeed.Feed(timezone=-5)
            self.assertTrue(False, "Exception expected")
        except Exception as e:
            self.assertTrue(str(e).find("timezone as an int parameter is not supported anymore") == 0)

        try:
            barFeed = yahoofeed.Feed()
            barFeed.addBarsFromCSV(
                INSTRUMENT, PRICE_CURRENCY, common.get_data_file_path("orcl-2000-yahoofinance.csv"),
                -3
            )
            self.assertTrue(False, "Exception expected")
        except Exception as e:
            self.assertTrue(str(e).find("timezone as an int parameter is not supported anymore") == 0)

    def testMapTypeOperations(self):
        barFeed = yahoofeed.Feed()
        barFeed.addBarsFromCSV(
            INSTRUMENT, PRICE_CURRENCY, common.get_data_file_path("orcl-2000-yahoofinance.csv"),
            marketsession.USEquities.getTimezone()
        )
        for dateTime, bars in barFeed:
            self.assertTrue(bar.pair_to_key(INSTRUMENT, PRICE_CURRENCY) in bars)
            self.assertTrue(INSTRUMENT not in bars)
            bars.getBar(INSTRUMENT, PRICE_CURRENCY)
            with self.assertRaises(KeyError):
                bars[bar.pair_to_key("pirulo", PRICE_CURRENCY)]

    def testBounded(self):
        barFeed = yahoofeed.Feed(maxLen=2)
        barFeed.addBarsFromCSV(
            INSTRUMENT, PRICE_CURRENCY, common.get_data_file_path("orcl-2000-yahoofinance.csv"),
            marketsession.USEquities.getTimezone()
        )
        for dateTime, bars in barFeed:
            pass

        barDS = barFeed.getDataSeries(INSTRUMENT, PRICE_CURRENCY)
        self.assertEqual(len(barDS), 2)
        self.assertEqual(len(barDS.getDateTimes()), 2)
        self.assertEqual(len(barDS.getCloseDataSeries()), 2)
        self.assertEqual(len(barDS.getCloseDataSeries().getDateTimes()), 2)
        self.assertEqual(len(barDS.getOpenDataSeries()), 2)
        self.assertEqual(len(barDS.getHighDataSeries()), 2)
        self.assertEqual(len(barDS.getLowDataSeries()), 2)
        self.assertEqual(len(barDS.getAdjCloseDataSeries()), 2)

    def testReset(self):
        barFeed = yahoofeed.Feed()
        barFeed.addBarsFromCSV(
            INSTRUMENT, PRICE_CURRENCY, common.get_data_file_path("orcl-2000-yahoofinance.csv"),
            marketsession.USEquities.getTimezone()
        )
        barFeed.loadAll()
        keys = barFeed.getKeys()
        ds = barFeed.getDataSeries(INSTRUMENT, PRICE_CURRENCY)

        barFeed.reset()
        barFeed.loadAll()
        reloadedDs = barFeed.getDataSeries(INSTRUMENT, PRICE_CURRENCY)

        self.assertEqual(len(reloadedDs), len(ds))
        self.assertNotEqual(reloadedDs, ds)
        self.assertEqual(keys, barFeed.getKeys())
        for i in range(len(ds)):
            self.assertEqual(ds[i].getDateTime(), reloadedDs[i].getDateTime())
            self.assertEqual(ds[i].getClose(), reloadedDs[i].getClose())
