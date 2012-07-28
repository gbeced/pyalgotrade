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
import os

from pyalgotrade.barfeed import csvfeed
from pyalgotrade.barfeed import ninjatraderfeed
# from pyalgotrade.providers.interactivebrokers import ibfeed
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
			self.__testcase.assertTrue(self.__barFeed.getDataSeries().getValue().getDateTime() == dateTime)
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
		parser = csvfeed.YahooRowParser()
		row = {"Date":date, "Close":0, "Open":0 , "High":0 , "Low":0 , "Volume":0 , "Adj Close":0}
		return parser.parseBar(row).getDateTime()

	def testParseDate_1(self):
		date = self.__parseDate("1950-1-1")
		self.assertTrue(date.day == 1)
		self.assertTrue(date.month == 1)
		self.assertTrue(date.year == 1950)

	def testParseDate_2(self):
		date = self.__parseDate("2000-1-1")
		self.assertTrue(date.day == 1)
		self.assertTrue(date.month == 1)
		self.assertTrue(date.year == 2000)

	def testDateCompare(self):
		self.assertTrue(self.__parseDate("2000-1-1") == self.__parseDate("2000-1-1"))
		self.assertTrue(self.__parseDate("2000-1-1") != self.__parseDate("2001-1-1"))
		self.assertTrue(self.__parseDate("1999-1-1") < self.__parseDate("2001-1-1"))
		self.assertTrue(self.__parseDate("2011-1-1") > self.__parseDate("2001-2-2"))

	def testCSVFeedLoadOrder(self):
		barFeed = csvfeed.YahooFeed()
		barFeed.addBarsFromCSV(YahooTestCase.TestInstrument, common.get_data_file_path("orcl-2000-yahoofinance.csv"))
		barFeed.addBarsFromCSV(YahooTestCase.TestInstrument, common.get_data_file_path("orcl-2001-yahoofinance.csv"))

		# Dispatch and handle events.
		handler = BarFeedEventHandler_TestLoadOrder(self, barFeed, YahooTestCase.TestInstrument)
		barFeed.getNewBarsEvent().subscribe(handler.onBars)
		while not barFeed.stopDispatching():
			barFeed.dispatch()
		self.assertTrue(handler.getEventCount() > 0)

	def __testFilteredRangeImpl(self, fromDate, toDate):
		barFeed = csvfeed.YahooFeed()
		barFeed.setBarFilter(csvfeed.DateRangeFilter(fromDate, toDate))
		barFeed.addBarsFromCSV(YahooTestCase.TestInstrument, common.get_data_file_path("orcl-2000-yahoofinance.csv"))
		barFeed.addBarsFromCSV(YahooTestCase.TestInstrument, common.get_data_file_path("orcl-2001-yahoofinance.csv"))

		# Dispatch and handle events.
		handler = BarFeedEventHandler_TestFilterRange(self, YahooTestCase.TestInstrument, fromDate, toDate)
		barFeed.getNewBarsEvent().subscribe(handler.onBars)
		while not barFeed.stopDispatching():
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

class IntradayBarFeedTestCase(unittest.TestCase):
	def __loadIntradayBarFeed(self):
		ret = ninjatraderfeed.Feed(ninjatraderfeed.Frequency.MINUTE)
		ret.addBarsFromCSV("spy", common.get_data_file_path("nt-spy-minute-2011.csv"))
		# This is need to get session close attributes set. Strategy class is responsible for calling this.
		ret.start()
		# Process all events to get the dataseries fully loaded.
		while not ret.stopDispatching():
			ret.dispatch()
		return ret

	def testSessionClose(self):
		barFeed = self.__loadIntradayBarFeed()
		ds = barFeed.getDataSeries()

		# Check that the first bar has session close set to False.
		self.assertTrue(ds.getValueAbsolute(0).getSessionClose() == False)

		# 670: 2011-01-03 23:57:00
		# 671: 2011-01-03 23:58:00
		# 672: 2011-01-04 00:01:00
		self.assertTrue(ds.getValueAbsolute(670).getSessionClose() == False)
		self.assertTrue(ds.getValueAbsolute(670).getBarsTillSessionClose() == 1)
		self.assertTrue(ds.getValueAbsolute(671).getSessionClose() == True)
		self.assertTrue(ds.getValueAbsolute(671).getBarsTillSessionClose() == 0)
		self.assertTrue(ds.getValueAbsolute(672).getSessionClose() == False)
		self.assertTrue(ds.getValueAbsolute(672).getBarsTillSessionClose() != 0)
		self.assertTrue(ds.getValueAbsolute(672).getBarsTillSessionClose() != 1)

		# Check that the last bar has session close set to True.
		self.assertTrue(ds.getValue().getBarsTillSessionClose() == 0)
		self.assertTrue(ds.getValue().getSessionClose() == True)

		# Check all bars.
		for i in xrange(ds.getLength()):
			currentBar = ds.getValueAbsolute(i)
			if currentBar.getSessionClose() == True:
				previousBar = ds.getValueAbsolute(i-1)
				self.assertTrue(previousBar.getSessionClose() == False)
				self.assertTrue(previousBar.getBarsTillSessionClose() == 1)

class IBTestCase(unittest.TestCase):
	TestInstrument = "orcl"

	def __parseDate(self, date):
		parser = ibfeed.RowParser("test")
		row = {"Date":date, "Close":0, "Open":0 , "High":0 , "Low":0 , "Volume":0 , "TradeCount":0 , "VWAP":0 , "HasGap": "False"}
		return parser.parseBar(row).getDateTime()

	def testParseDate_1(self):
		date = self.__parseDate("2012-06-29 01:55:00")
		self.assertTrue(date.day == 29)
		self.assertTrue(date.month == 06)
		self.assertTrue(date.year == 2012)

		self.assertTrue(date.hour == 01)
		self.assertTrue(date.minute == 55)
		self.assertTrue(date.second == 00)

	def testDateCompare(self):
		self.assertTrue(self.__parseDate("2012-06-29 00:55:00") != self.__parseDate("2012-06-29 01:55:00"))
		self.assertTrue(self.__parseDate("2011-06-29 00:55:00") < self.__parseDate("2012-06-29 01:55:00"))
		self.assertTrue(self.__parseDate("2012-06-29 00:55:00") < self.__parseDate("2012-06-29 01:55:00"))

	def testCSVFeedLoadOrder(self):
		barFeed = ibfeed.CSVFeed()
		barFeed.addBarsFromCSV(IBTestCase.TestInstrument, common.get_data_file_path("ib-spy-5min-20120627.csv"))
		barFeed.addBarsFromCSV(IBTestCase.TestInstrument, common.get_data_file_path("ib-spy-5min-20120628.csv"))
		barFeed.addBarsFromCSV(IBTestCase.TestInstrument, common.get_data_file_path("ib-spy-5min-20120629.csv"))

		handler = BarFeedEventHandler_TestLoadOrder(self, barFeed, IBTestCase.TestInstrument)
		barFeed.getNewBarsEvent().subscribe(handler.onBars)
		while not barFeed.stopDispatching():
			barFeed.dispatch()
		self.assertTrue(handler.getEventCount() > 0)

	def __testFilteredRangeImpl(self, fromDate, toDate):
		barFeed = ibfeed.CSVFeed()
		barFeed.setBarFilter(csvfeed.DateRangeFilter(fromDate, toDate))
		barFeed.addBarsFromCSV(IBTestCase.TestInstrument, common.get_data_file_path("ib-spy-5min-20120627.csv"))
		barFeed.addBarsFromCSV(IBTestCase.TestInstrument, common.get_data_file_path("ib-spy-5min-20120628.csv"))
		barFeed.addBarsFromCSV(IBTestCase.TestInstrument, common.get_data_file_path("ib-spy-5min-20120629.csv"))
		
		# Dispatch and handle events.
		handler = BarFeedEventHandler_TestFilterRange(self, IBTestCase.TestInstrument, fromDate, toDate)
		barFeed.getNewBarsEvent().subscribe(handler.onBars)
		while not barFeed.stopDispatching():
			barFeed.dispatch()
		self.assertTrue(handler.getEventCount() > 0)

	def testFilteredRangeFrom(self):
		self.__testFilteredRangeImpl(datetime.datetime(2012, 06, 28, 00, 00), None)

	def testFilteredRangeTo(self):
		self.__testFilteredRangeImpl(None, datetime.datetime(2012, 06, 29, 23, 55))

	def testFilteredRangeFromTo(self):
		self.__testFilteredRangeImpl(datetime.datetime(2000, 1, 1, 00, 00), datetime.datetime(2020, 12, 31, 23, 55))

def getTestCases():
	ret = []
	ret.append(YahooTestCase("testParseDate_1"))
	ret.append(YahooTestCase("testParseDate_2"))
	ret.append(YahooTestCase("testDateCompare"))
	ret.append(YahooTestCase("testCSVFeedLoadOrder"))
	ret.append(YahooTestCase("testFilteredRangeFrom"))
	ret.append(YahooTestCase("testFilteredRangeTo"))
	ret.append(YahooTestCase("testFilteredRangeFromTo"))
	ret.append(IntradayBarFeedTestCase("testSessionClose"))
	# ret.append(IBTestCase("testParseDate_1"))
	# ret.append(IBTestCase("testDateCompare"))
	# ret.append(IBTestCase("testCSVFeedLoadOrder"))
	# ret.append(IBTestCase("testFilteredRangeFrom"))
	# ret.append(IBTestCase("testFilteredRangeTo"))
	# ret.append(IBTestCase("testFilteredRangeFromTo"))
	return ret


# vim: noet:ci:pi:sts=0:sw=4:ts=4
