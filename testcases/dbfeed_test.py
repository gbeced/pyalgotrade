# PyAlgoTrade
# 
# Copyright 2012 Gabriel Martin Becedillas Ruiz
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
import os

from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.barfeed import sqlitefeed
from pyalgotrade import barfeed
from pyalgotrade import dataseries
from pyalgotrade import marketsession
import common

class TemporarySQLiteFeed:
	def __init__(self, dbFilePath, frequency, maxLen=dataseries.DEFAULT_MAX_LEN):
		if os.path.exists(dbFilePath):
			raise Exception("File exists")

		self.__dbFilePath = dbFilePath
		self.__frequency = frequency
		self.__feed = None
		self.__maxLen = maxLen

	def __enter__(self):
		self.__feed = sqlitefeed.Feed(self.__dbFilePath, self.__frequency, maxLen=self.__maxLen)

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.__feed = None
		os.remove(self.__dbFilePath)

	def getFeed(self):
		return self.__feed

class SQLiteFeedTestCase(unittest.TestCase):
	dbName = "SQLiteFeedTestCase.sqlite"

	def testLoadDailyBars(self):
		tmpFeed = TemporarySQLiteFeed(SQLiteFeedTestCase.dbName, barfeed.Frequency.DAY)
		with tmpFeed:
			# Load bars using a Yahoo! feed.
			yahooFeed = yahoofeed.Feed()
			yahooFeed.addBarsFromCSV("orcl", common.get_data_file_path("orcl-2000-yahoofinance.csv"), marketsession.USEquities.timezone)
			yahooFeed.addBarsFromCSV("orcl", common.get_data_file_path("orcl-2001-yahoofinance.csv"), marketsession.USEquities.timezone)

			# Fill the database using the bars from the Yahoo! feed.
			sqliteFeed = tmpFeed.getFeed()
			sqliteFeed.getDatabase().addBarsFromFeed(yahooFeed)

			# Load the SQLite feed and process all bars.
			sqliteFeed.loadBars("orcl")
			sqliteFeed.start()
			for bars in sqliteFeed:
				pass
			sqliteFeed.stop()
			sqliteFeed.join()

			# Check that both dataseries have the same bars.
			yahooDS = yahooFeed["orcl"]
			sqliteDS = sqliteFeed["orcl"]
			self.assertEqual(len(yahooDS), len(sqliteDS))
			for i in xrange(len(yahooDS)):
				self.assertEqual(yahooDS[i].getDateTime(), sqliteDS[i].getDateTime())
				self.assertEqual(yahooDS[i].getOpen(), sqliteDS[i].getOpen())
				self.assertEqual(yahooDS[i].getHigh(), sqliteDS[i].getHigh())
				self.assertEqual(yahooDS[i].getLow(), sqliteDS[i].getLow())
				self.assertEqual(yahooDS[i].getClose(), sqliteDS[i].getClose())
				self.assertEqual(yahooDS[i].getAdjClose(), sqliteDS[i].getAdjClose())
				self.assertEqual(yahooDS[i].getBarsTillSessionClose(), sqliteDS[i].getBarsTillSessionClose())
				self.assertEqual(yahooDS[i].getSessionClose(), sqliteDS[i].getSessionClose())

	def testBounded(self):
		tmpFeed = TemporarySQLiteFeed(SQLiteFeedTestCase.dbName, barfeed.Frequency.DAY, maxLen=2)
		with tmpFeed:
			# Load bars using a Yahoo! feed.
			yahooFeed = yahoofeed.Feed(maxLen=1)
			yahooFeed.addBarsFromCSV("orcl", common.get_data_file_path("orcl-2000-yahoofinance.csv"), marketsession.USEquities.timezone)
			yahooFeed.addBarsFromCSV("orcl", common.get_data_file_path("orcl-2001-yahoofinance.csv"), marketsession.USEquities.timezone)

			# Fill the database using the bars from the Yahoo! feed.
			sqliteFeed = tmpFeed.getFeed()
			sqliteFeed.getDatabase().addBarsFromFeed(yahooFeed)

			# Load the SQLite feed and process all bars.
			sqliteFeed.loadBars("orcl")
			sqliteFeed.start()
			for bars in sqliteFeed:
				pass
			sqliteFeed.stop()
			sqliteFeed.join()

			barDS = sqliteFeed["orcl"]
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

	ret.append(SQLiteFeedTestCase("testLoadDailyBars"))
	ret.append(SQLiteFeedTestCase("testBounded"))

	return ret

