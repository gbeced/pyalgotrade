# PyAlgoTrade
# 
# Copyright 2011 Gabriel Martin Becedillas Ruiz
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#	http://www.apache.org/licenses/LICENSE-2.0
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
import datetime

from pyalgotrade.barfeed import csvfeed
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.barfeed import ninjatraderfeed
from pyalgotrade.utils import dt
from pyalgotrade import marketsession
import common

class BarFeedEventHandler_TestLoadOrder:
	def __init__(self, testcase, barFeed, instrument):
		self.__testcase = testcase
		self.__count = 0
		self.__prevDateTime = None
		self.__barFeed = barFeed
		self.__instrument = instrument

	def onBars(self, bars):
		self.__count += 1
		dateTime = bars.getBar(self.__instrument).getDateTime()
		if self.__prevDateTime != None:
			# Check that bars are loaded in order
			self.__testcase.assertTrue(self.__prevDateTime < dateTime)
			# Check that the last value in the dataseries match the current datetime.
			self.__testcase.assertTrue(self.__barFeed.getDataSeries()[-1].getDateTime() == dateTime)
			# Check that the datetime for the last value matches that last datetime in the dataseries.
			self.__testcase.assertEqual(self.__barFeed.getDataSeries()[-1].getDateTime(), self.__barFeed.getDataSeries().getDateTimes()[-1])
		self.__prevDateTime = dateTime

	def getEventCount(self):
			return self.__count
	
class BarFeedEventHandler_TestFilterRange:
	def __init__(self, testcase, instrument, fromDate, toDate):
		self.__testcase = testcase
		self.__count = 0
		self.__instrument = instrument
		self.__fromDate = fromDate
		self.__toDate = toDate

	def onBars(self, bars):
		self.__count += 1

		if self.__fromDate != None:
			self.__testcase.assertTrue(bars.getBar(self.__instrument).getDateTime() >= self.__fromDate)
		if self.__toDate != None:
			self.__testcase.assertTrue(bars.getBar(self.__instrument).getDateTime() <= self.__toDate)

	def getEventCount(self):
			return self.__count

class YahooTestCase(unittest.TestCase):
	TestInstrument = "orcl"

	def __parseDate(self, date):
		parser = yahoofeed.RowParser(datetime.time(23, 59))
		row = {"Date":date, "Close":0, "Open":0 , "High":0 , "Low":0 , "Volume":0 , "Adj Close":0}
		return parser.parseBar(row).getDateTime()

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
		barFeed.addBarsFromCSV(YahooTestCase.TestInstrument, common.get_data_file_path("orcl-2000-yahoofinance.csv"))
		barFeed.addBarsFromCSV(YahooTestCase.TestInstrument, common.get_data_file_path("orcl-2001-yahoofinance.csv"))

		# Dispatch and handle events.
		handler = BarFeedEventHandler_TestLoadOrder(self, barFeed, YahooTestCase.TestInstrument)
		barFeed.getNewBarsEvent().subscribe(handler.onBars)
		while not barFeed.eof():
			barFeed.dispatch()
		self.assertTrue(handler.getEventCount() > 0)

	def __testFilteredRangeImpl(self, fromDate, toDate):
		barFeed = yahoofeed.Feed()
		barFeed.setBarFilter(csvfeed.DateRangeFilter(fromDate, toDate))
		barFeed.addBarsFromCSV(YahooTestCase.TestInstrument, common.get_data_file_path("orcl-2000-yahoofinance.csv"))
		barFeed.addBarsFromCSV(YahooTestCase.TestInstrument, common.get_data_file_path("orcl-2001-yahoofinance.csv"))

		# Dispatch and handle events.
		handler = BarFeedEventHandler_TestFilterRange(self, YahooTestCase.TestInstrument, fromDate, toDate)
		barFeed.getNewBarsEvent().subscribe(handler.onBars)
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
		barFeed.addBarsFromCSV(YahooTestCase.TestInstrument, common.get_data_file_path("orcl-2000-yahoofinance.csv"))
		barFeed.addBarsFromCSV(YahooTestCase.TestInstrument, common.get_data_file_path("orcl-2001-yahoofinance.csv"))
		barFeed.start()
		for bars in barFeed:
			bar = bars.getBar(YahooTestCase.TestInstrument)
			self.assertTrue(dt.datetime_is_naive(bar.getDateTime()))
		barFeed.stop()
		barFeed.join()

	def testWithDefaultTimezone(self):
		barFeed = yahoofeed.Feed(marketsession.USEquities.getTimezone())
		barFeed.addBarsFromCSV(YahooTestCase.TestInstrument, common.get_data_file_path("orcl-2000-yahoofinance.csv"))
		barFeed.addBarsFromCSV(YahooTestCase.TestInstrument, common.get_data_file_path("orcl-2001-yahoofinance.csv"))
		barFeed.start()
		for bars in barFeed:
			bar = bars.getBar(YahooTestCase.TestInstrument)
			self.assertFalse(dt.datetime_is_naive(bar.getDateTime()))
		barFeed.stop()
		barFeed.join()

	def testWithPerFileTimezone(self):
		barFeed = yahoofeed.Feed()
		barFeed.addBarsFromCSV(YahooTestCase.TestInstrument, common.get_data_file_path("orcl-2000-yahoofinance.csv"), marketsession.USEquities.getTimezone())
		barFeed.addBarsFromCSV(YahooTestCase.TestInstrument, common.get_data_file_path("orcl-2001-yahoofinance.csv"), marketsession.USEquities.getTimezone())
		barFeed.start()
		for bars in barFeed:
			bar = bars.getBar(YahooTestCase.TestInstrument)
			self.assertFalse(dt.datetime_is_naive(bar.getDateTime()))
		barFeed.stop()
		barFeed.join()

	def testWithIntegerTimezone(self):
		try:
			barFeed = yahoofeed.Feed(-5)
			self.assertTrue(False, "Exception expected")
		except Exception, e:
			self.assertTrue(str(e).find("timezone as an int parameter is not supported anymore") == 0)

		try:
			barFeed = yahoofeed.Feed()
			barFeed.addBarsFromCSV(YahooTestCase.TestInstrument, common.get_data_file_path("orcl-2000-yahoofinance.csv"), -3)
			self.assertTrue(False, "Exception expected")
		except Exception, e:
			self.assertTrue(str(e).find("timezone as an int parameter is not supported anymore") == 0)

	def testMapTypeOperations(self):
		barFeed = yahoofeed.Feed()
		barFeed.addBarsFromCSV(YahooTestCase.TestInstrument, common.get_data_file_path("orcl-2000-yahoofinance.csv"), marketsession.USEquities.getTimezone())
		barFeed.start()
		for bars in barFeed:
			self.assertTrue(YahooTestCase.TestInstrument in bars)
			self.assertFalse(YahooTestCase.TestInstrument not in bars)
			bars[YahooTestCase.TestInstrument]
			with self.assertRaises(KeyError):
				bars["pirulo"]
		barFeed.stop()
		barFeed.join()

	def testBounded(self):
		barFeed = yahoofeed.Feed(maxLen=2)
		barFeed.addBarsFromCSV(YahooTestCase.TestInstrument, common.get_data_file_path("orcl-2000-yahoofinance.csv"), marketsession.USEquities.getTimezone())
		barFeed.start()
		for bars in barFeed:
			pass
		barFeed.stop()
		barFeed.join()

		barDS = barFeed[YahooTestCase.TestInstrument]
		self.assertEqual(len(barDS), 2)
		self.assertEqual(len(barDS.getDateTimes()), 2)
		self.assertEqual(len(barDS.getCloseDataSeries()), 2)
		self.assertEqual(len(barDS.getCloseDataSeries().getDateTimes()), 2)
		self.assertEqual(len(barDS.getOpenDataSeries()), 2)
		self.assertEqual(len(barDS.getHighDataSeries()), 2)
		self.assertEqual(len(barDS.getLowDataSeries()), 2)
		self.assertEqual(len(barDS.getAdjCloseDataSeries()), 2)

class NinjaTraderTestCase(unittest.TestCase):
	def __loadIntradayBarFeed(self, timeZone = None):
		ret = ninjatraderfeed.Feed(ninjatraderfeed.Frequency.MINUTE, timeZone)
		ret.addBarsFromCSV("spy", common.get_data_file_path("nt-spy-minute-2011.csv"))
		ret.loadAll()
		return ret

	def testWithTimezone(self):
		timeZone = marketsession.USEquities.getTimezone()
		barFeed = self.__loadIntradayBarFeed(timeZone)
		ds = barFeed.getDataSeries()

		for i in xrange(ds.getLength()):
			currentBar = ds[i]
			self.assertFalse(dt.datetime_is_naive(currentBar.getDateTime()))
			self.assertEqual(ds[i].getDateTime(), ds.getDateTimes()[i])

	def testWithoutTimezone(self):
		barFeed = self.__loadIntradayBarFeed(None)
		ds = barFeed.getDataSeries()

		for i in xrange(ds.getLength()):
			currentBar = ds[i]
			# Datetime must be set to UTC.
			self.assertFalse(dt.datetime_is_naive(currentBar.getDateTime()))
			self.assertEqual(ds[i].getDateTime(), ds.getDateTimes()[i])

	def testWithIntegerTimezone(self):
		try:
			barFeed = ninjatraderfeed.Feed(ninjatraderfeed.Frequency.MINUTE, -3)
			self.assertTrue(False, "Exception expected")
		except Exception, e:
			self.assertTrue(str(e).find("timezone as an int parameter is not supported anymore") == 0)

		try:
			barFeed = ninjatraderfeed.Feed(ninjatraderfeed.Frequency.MINUTE)
			barFeed.addBarsFromCSV("spy", common.get_data_file_path("nt-spy-minute-2011.csv"), -5)
			self.assertTrue(False, "Exception expected")
		except Exception, e:
			self.assertTrue(str(e).find("timezone as an int parameter is not supported anymore") == 0)

	def testLocalizeAndFilter(self):
		timezone = marketsession.USEquities.getTimezone()
		# The prices come from NinjaTrader interface when set to use 'US Equities RTH' session template.
		prices = {
			dt.localize(datetime.datetime(2011, 3, 9, 9, 31), timezone) : 132.35,
			dt.localize(datetime.datetime(2011, 3, 9, 16), timezone) : 132.39,
			dt.localize(datetime.datetime(2011, 3, 10, 9, 31), timezone) : 130.81,
			dt.localize(datetime.datetime(2011, 3, 10, 16), timezone) : 129.92,
			dt.localize(datetime.datetime(2011, 3, 11, 9, 31), timezone) : 129.72,
			dt.localize(datetime.datetime(2011, 3, 11, 16), timezone) : 130.84,
		}
		barFeed = ninjatraderfeed.Feed(ninjatraderfeed.Frequency.MINUTE, timezone)
		barFeed.addBarsFromCSV("spy", common.get_data_file_path("nt-spy-minute-2011-03.csv"))
		for bars in barFeed:
			price = prices.get(bars.getDateTime(), None)
			if price != None:
				self.assertTrue(price == bars.getBar("spy").getClose())

	def testBounded(self):
		barFeed = ninjatraderfeed.Feed(ninjatraderfeed.Frequency.MINUTE, maxLen=2)
		barFeed.addBarsFromCSV("spy", common.get_data_file_path("nt-spy-minute-2011-03.csv"))
		barFeed.loadAll()

		barDS = barFeed["spy"]
		self.assertEqual(len(barDS), 2)
		self.assertEqual(len(barDS.getDateTimes()), 2)
		self.assertEqual(len(barDS.getCloseDataSeries()), 2)
		self.assertEqual(len(barDS.getCloseDataSeries().getDateTimes()), 2)
		self.assertEqual(len(barDS.getOpenDataSeries()), 2)
		self.assertEqual(len(barDS.getHighDataSeries()), 2)
		self.assertEqual(len(barDS.getLowDataSeries()), 2)
		self.assertEqual(len(barDS.getAdjCloseDataSeries()), 2)

def getTestCases():
	ret = []

	ret.append(YahooTestCase("testParseDate_1"))
	ret.append(YahooTestCase("testParseDate_2"))
	ret.append(YahooTestCase("testDateCompare"))
	ret.append(YahooTestCase("testCSVFeedLoadOrder"))
	ret.append(YahooTestCase("testFilteredRangeFrom"))
	ret.append(YahooTestCase("testFilteredRangeTo"))
	ret.append(YahooTestCase("testFilteredRangeFromTo"))
	ret.append(YahooTestCase("testWithoutTimezone"))
	ret.append(YahooTestCase("testWithDefaultTimezone"))
	ret.append(YahooTestCase("testWithPerFileTimezone"))
	ret.append(YahooTestCase("testWithIntegerTimezone"))
	ret.append(YahooTestCase("testMapTypeOperations"))
	ret.append(YahooTestCase("testBounded"))

	ret.append(NinjaTraderTestCase("testWithTimezone"))
	ret.append(NinjaTraderTestCase("testWithoutTimezone"))
	ret.append(NinjaTraderTestCase("testWithIntegerTimezone"))
	ret.append(NinjaTraderTestCase("testLocalizeAndFilter"))
	ret.append(NinjaTraderTestCase("testBounded"))

	return ret

