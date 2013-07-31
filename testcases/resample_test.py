# PyAlgoTrade
# 
# Copyright 2013 Gabriel Martin Becedillas Ruiz
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
import datetime

from pyalgotrade import barfeed
import pyalgotrade.mtgox.barfeed as mtgoxfeed 
from pyalgotrade.barfeed import ninjatraderfeed
from pyalgotrade.barfeed import csvfeed
from pyalgotrade.tools import resample
from pyalgotrade import marketsession
from pyalgotrade.utils import dt
import common

class ResampleTestCase(unittest.TestCase):
	def testResampleMtGoxMinute(self):
		# Resample.
		feed = mtgoxfeed.CSVTradeFeed()
		feed.addBarsFromCSV(common.get_data_file_path("trades-mgtox-usd-2013-01-01.csv"))
		resample.resample_minute(feed, "minute-mgtox-usd-2013-01-01.csv")

		# Load the resampled file.
		feed = csvfeed.GenericBarFeed(barfeed.Frequency.MINUTE)
		feed.addBarsFromCSV("BTC", "minute-mgtox-usd-2013-01-01.csv")
		feed.loadAll()
		
		self.assertEqual(len(feed["BTC"]), 537)
		self.assertEqual(feed["BTC"][0].getDateTime(), datetime.datetime(2013, 01, 01, 00, 04, 59))
		self.assertEqual(feed["BTC"][-1].getDateTime(), datetime.datetime(2013, 01, 01, 23, 58, 59))

	def testResampleMtGoxHour(self):
		# Resample.
		feed = mtgoxfeed.CSVTradeFeed()
		feed.addBarsFromCSV(common.get_data_file_path("trades-mgtox-usd-2013-01-01.csv"))
		resample.resample_hour(feed, "hour-mgtox-usd-2013-01-01.csv")

		# Load the resampled file.
		feed = csvfeed.GenericBarFeed(barfeed.Frequency.HOUR)
		feed.addBarsFromCSV("BTC", "hour-mgtox-usd-2013-01-01.csv")
		feed.loadAll()
	
		self.assertEqual(len(feed["BTC"]), 24)
		self.assertEqual(feed["BTC"][0].getDateTime(), datetime.datetime(2013, 01, 01, 00, 59, 59))
		self.assertEqual(feed["BTC"][-1].getDateTime(), datetime.datetime(2013, 01, 01, 23, 59, 59))

	def testResampleMtGoxDay(self):
		# Resample.
		feed = mtgoxfeed.CSVTradeFeed()
		feed.addBarsFromCSV(common.get_data_file_path("trades-mgtox-usd-2013-01-01.csv"))
		resample.resample_day(feed, "day-mgtox-usd-2013-01-01.csv")

		# Load the resampled file.
		feed = csvfeed.GenericBarFeed(barfeed.Frequency.DAY)
		feed.addBarsFromCSV("BTC", "day-mgtox-usd-2013-01-01.csv")
		feed.loadAll()
	
		self.assertEqual(len(feed["BTC"]), 1)
		self.assertEqual(feed["BTC"][0].getDateTime(), datetime.datetime(2013, 01, 01, 23, 59, 59))
		self.assertEqual(feed["BTC"][0].getOpen(), 13.51001)
		self.assertEqual(feed["BTC"][0].getHigh(), 13.56)
		self.assertEqual(feed["BTC"][0].getLow(), 13.16123)
		self.assertEqual(feed["BTC"][0].getClose(), 13.30413)
		self.assertEqual(feed["BTC"][0].getVolume(), 28168.9114596)
		self.assertEqual(feed["BTC"][0].getAdjClose(), 13.51001)

	def testResampleNinjaTraderHour(self):
		# Resample.
		feed = ninjatraderfeed.Feed(ninjatraderfeed.Frequency.MINUTE)
		feed.addBarsFromCSV("spy", common.get_data_file_path("nt-spy-minute-2011.csv"))
		resample.resample_hour(feed, "hour-nt-spy-minute-2011.csv")

		# Load the resampled file.
		feed = csvfeed.GenericBarFeed(barfeed.Frequency.HOUR, marketsession.USEquities.getTimezone())
		feed.addBarsFromCSV("spy", "hour-nt-spy-minute-2011.csv")
		feed.loadAll()

		self.assertEqual(len(feed["spy"]), 340)
		self.assertEqual(feed["spy"][0].getDateTime(), dt.localize(datetime.datetime(2011, 01, 03, 9, 59, 59), marketsession.USEquities.getTimezone()))
		self.assertEqual(feed["spy"][-1].getDateTime(), dt.localize(datetime.datetime(2011, 02, 01, 01, 59, 59), marketsession.USEquities.getTimezone()))
		self.assertEqual(feed["spy"][0].getOpen(), 126.35)
		self.assertEqual(feed["spy"][0].getHigh(), 126.45)
		self.assertEqual(feed["spy"][0].getLow(), 126.3)
		self.assertEqual(feed["spy"][0].getClose(), 126.4)
		self.assertEqual(feed["spy"][0].getVolume(), 3397.0)
		self.assertEqual(feed["spy"][0].getAdjClose(), None)

	def testResampleNinjaTraderDay(self):
		# Resample.
		feed = ninjatraderfeed.Feed(ninjatraderfeed.Frequency.MINUTE)
		feed.addBarsFromCSV("spy", common.get_data_file_path("nt-spy-minute-2011.csv"))
		resample.resample_day(feed, "day-nt-spy-minute-2011.csv")

		# Load the resampled file.
		feed = csvfeed.GenericBarFeed(barfeed.Frequency.DAY)
		feed.addBarsFromCSV("spy", "day-nt-spy-minute-2011.csv", marketsession.USEquities.getTimezone())
		feed.loadAll()
	
		self.assertEqual(len(feed["spy"]), 25)
		self.assertEqual(feed["spy"][0].getDateTime(), dt.localize(datetime.datetime(2011, 01, 03, 23, 59, 59), marketsession.USEquities.getTimezone()))
		self.assertEqual(feed["spy"][-1].getDateTime(), dt.localize(datetime.datetime(2011, 02, 01, 23, 59, 59), marketsession.USEquities.getTimezone()))

def getTestCases():
	ret = []

	ret.append(ResampleTestCase("testResampleMtGoxMinute"))
	ret.append(ResampleTestCase("testResampleMtGoxHour"))
	ret.append(ResampleTestCase("testResampleMtGoxDay"))
	ret.append(ResampleTestCase("testResampleNinjaTraderHour"))
	ret.append(ResampleTestCase("testResampleNinjaTraderDay"))

	return ret

