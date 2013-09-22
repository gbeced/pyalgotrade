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
import os

from pyalgotrade import barfeed
import pyalgotrade.mtgox.barfeed as mtgoxfeed 
from pyalgotrade.barfeed import ninjatraderfeed
from pyalgotrade.barfeed import csvfeed
from pyalgotrade.tools import resample
from pyalgotrade import marketsession
from pyalgotrade.utils import dt
from pyalgotrade.dataseries import resampled
from pyalgotrade.dataseries import bards
from pyalgotrade import bar
import common

class ResampleTestCase(unittest.TestCase):
	def testResample(self):
		barDs = bards.BarDataSeries()
		resampledBarDS = resampled.ResampledBarDataSeries(barDs, barfeed.Frequency.MINUTE)

		barDs.append(bar.BasicBar(datetime.datetime(2011, 1, 1, 1, 1, 1), 2.1, 3, 1, 2, 10, 1))
		barDs.append(bar.BasicBar(datetime.datetime(2011, 1, 1, 1, 1, 2), 2, 3, 1, 2.3, 10, 2))
		barDs.append(bar.BasicBar(datetime.datetime(2011, 1, 1, 1, 2, 1), 2, 3, 1, 2, 10, 2))

		self.assertEqual(len(resampledBarDS), 1)
		self.assertEqual(resampledBarDS[0].getDateTime(), datetime.datetime(2011, 1, 1, 1, 1, 59))
		self.assertEqual(resampledBarDS[0].getOpen(), 2.1)
		self.assertEqual(resampledBarDS[0].getHigh(), 3)
		self.assertEqual(resampledBarDS[0].getLow(), 1)
		self.assertEqual(resampledBarDS[0].getClose(), 2.3)
		self.assertEqual(resampledBarDS[0].getVolume(), 20)
		self.assertEqual(resampledBarDS[0].getAdjClose(), 2)

		resampledBarDS.pushLast()
		self.assertEqual(len(resampledBarDS), 2)
		self.assertEqual(resampledBarDS[1].getDateTime(), datetime.datetime(2011, 1, 1, 1, 2, 59))
		self.assertEqual(resampledBarDS[1].getOpen(), 2)
		self.assertEqual(resampledBarDS[1].getHigh(), 3)
		self.assertEqual(resampledBarDS[1].getLow(), 1)
		self.assertEqual(resampledBarDS[1].getClose(), 2)
		self.assertEqual(resampledBarDS[1].getVolume(), 10)
		self.assertEqual(resampledBarDS[1].getAdjClose(), 2)


	def testResampleMtGoxMinute(self):
		# Resample.
		feed = mtgoxfeed.CSVTradeFeed()
		feed.addBarsFromCSV(common.get_data_file_path("trades-mgtox-usd-2013-01-01.csv"))
		resampledBarDS = resampled.ResampledBarDataSeries(feed["BTC"], barfeed.Frequency.MINUTE)
		resampledFile = os.path.join(common.get_temp_path(), "minute-mgtox-usd-2013-01-01.csv")
		resample.resample_to_csv(feed, barfeed.Frequency.MINUTE, resampledFile)
		resampledBarDS.pushLast() # Need to manually push the last stot since time didn't change.

		# Load the resampled file.
		feed = csvfeed.GenericBarFeed(barfeed.Frequency.MINUTE)
		feed.addBarsFromCSV("BTC", resampledFile)
		feed.loadAll()
		
		self.assertEqual(len(feed["BTC"]), 537)
		self.assertEqual(feed["BTC"][0].getDateTime(), datetime.datetime(2013, 01, 01, 00, 04, 59))
		self.assertEqual(feed["BTC"][-1].getDateTime(), datetime.datetime(2013, 01, 01, 23, 58, 59))

		self.assertEqual(len(resampledBarDS), len(feed["BTC"]))
		self.assertEqual(resampledBarDS[0].getDateTime(), dt.as_utc(feed["BTC"][0].getDateTime()))
		self.assertEqual(resampledBarDS[-1].getDateTime(), dt.as_utc(feed["BTC"][-1].getDateTime()))

	def testResampleMtGoxHour(self):
		# Resample.
		feed = mtgoxfeed.CSVTradeFeed()
		feed.addBarsFromCSV(common.get_data_file_path("trades-mgtox-usd-2013-01-01.csv"))
		resampledBarDS = resampled.ResampledBarDataSeries(feed["BTC"], barfeed.Frequency.HOUR)
		resampledFile = os.path.join(common.get_temp_path(), "hour-mgtox-usd-2013-01-01.csv")
		resample.resample_to_csv(feed, barfeed.Frequency.HOUR, resampledFile)
		resampledBarDS.pushLast() # Need to manually push the last stot since time didn't change.

		# Load the resampled file.
		feed = csvfeed.GenericBarFeed(barfeed.Frequency.HOUR)
		feed.addBarsFromCSV("BTC", resampledFile)
		feed.loadAll()
	
		self.assertEqual(len(feed["BTC"]), 24)
		self.assertEqual(feed["BTC"][0].getDateTime(), datetime.datetime(2013, 01, 01, 00, 59, 59))
		self.assertEqual(feed["BTC"][-1].getDateTime(), datetime.datetime(2013, 01, 01, 23, 59, 59))

		self.assertEqual(len(resampledBarDS), len(feed["BTC"]))
		self.assertEqual(resampledBarDS[0].getDateTime(), dt.as_utc(feed["BTC"][0].getDateTime()))
		self.assertEqual(resampledBarDS[-1].getDateTime(), dt.as_utc(feed["BTC"][-1].getDateTime()))

	def testResampleMtGoxDay(self):
		# Resample.
		feed = mtgoxfeed.CSVTradeFeed()
		feed.addBarsFromCSV(common.get_data_file_path("trades-mgtox-usd-2013-01-01.csv"))
		resampledBarDS = resampled.ResampledBarDataSeries(feed["BTC"], barfeed.Frequency.DAY)
		resampledFile = os.path.join(common.get_temp_path(), "day-mgtox-usd-2013-01-01.csv")
		resample.resample_to_csv(feed, barfeed.Frequency.DAY, resampledFile)
		resampledBarDS.pushLast() # Need to manually push the last stot since time didn't change.

		# Load the resampled file.
		feed = csvfeed.GenericBarFeed(barfeed.Frequency.DAY)
		feed.addBarsFromCSV("BTC", resampledFile)
		feed.loadAll()
	
		self.assertEqual(len(feed["BTC"]), 1)
		self.assertEqual(feed["BTC"][0].getDateTime(), datetime.datetime(2013, 01, 01, 23, 59, 59))
		self.assertEqual(feed["BTC"][0].getOpen(), 13.51001)
		self.assertEqual(feed["BTC"][0].getHigh(), 13.56)
		self.assertEqual(feed["BTC"][0].getLow(), 13.16123)
		self.assertEqual(feed["BTC"][0].getClose(), 13.30413)
		self.assertEqual(feed["BTC"][0].getVolume(), 28168.9114596)
		self.assertEqual(feed["BTC"][0].getAdjClose(), 13.30413)

		self.assertEqual(len(resampledBarDS), len(feed["BTC"]))
		self.assertEqual(resampledBarDS[0].getDateTime(), dt.as_utc(feed["BTC"][0].getDateTime()))
		self.assertEqual(resampledBarDS[-1].getDateTime(), dt.as_utc(feed["BTC"][-1].getDateTime()))
		self.assertEqual(resampledBarDS[0].getOpen(), feed["BTC"][0].getOpen())
		self.assertEqual(resampledBarDS[0].getHigh(), feed["BTC"][0].getHigh())
		self.assertEqual(resampledBarDS[0].getLow(), feed["BTC"][0].getLow())
		self.assertEqual(resampledBarDS[0].getClose(), feed["BTC"][0].getClose())
		self.assertEqual(round(resampledBarDS[0].getVolume(), 5), round(feed["BTC"][0].getVolume(), 5))
		self.assertEqual(resampledBarDS[0].getAdjClose(), feed["BTC"][0].getAdjClose())

	def testResampleNinjaTraderHour(self):
		# Resample.
		feed = ninjatraderfeed.Feed(ninjatraderfeed.Frequency.MINUTE)
		feed.addBarsFromCSV("spy", common.get_data_file_path("nt-spy-minute-2011.csv"))
		resampledBarDS = resampled.ResampledBarDataSeries(feed["spy"], barfeed.Frequency.HOUR)
		resampledFile = os.path.join(common.get_temp_path(), "hour-nt-spy-minute-2011.csv")
		resample.resample_to_csv(feed, barfeed.Frequency.HOUR, resampledFile)
		resampledBarDS.pushLast() # Need to manually push the last stot since time didn't change.

		# Load the resampled file.
		feed = csvfeed.GenericBarFeed(barfeed.Frequency.HOUR, marketsession.USEquities.getTimezone())
		feed.addBarsFromCSV("spy", resampledFile)
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

		self.assertEqual(len(resampledBarDS), len(feed["spy"]))
		self.assertEqual(resampledBarDS[0].getDateTime(), dt.as_utc(datetime.datetime(2011, 01, 03, 9, 59, 59)))
		self.assertEqual(resampledBarDS[-1].getDateTime(), dt.as_utc(datetime.datetime(2011, 02, 01, 01, 59, 59)))

	def testResampleNinjaTraderDay(self):
		# Resample.
		feed = ninjatraderfeed.Feed(ninjatraderfeed.Frequency.MINUTE)
		feed.addBarsFromCSV("spy", common.get_data_file_path("nt-spy-minute-2011.csv"))
		resampledBarDS = resampled.ResampledBarDataSeries(feed["spy"], barfeed.Frequency.DAY)
		resampledFile = os.path.join(common.get_temp_path(), "day-nt-spy-minute-2011.csv")
		resample.resample_to_csv(feed, barfeed.Frequency.DAY, resampledFile)
		resampledBarDS.pushLast() # Need to manually push the last stot since time didn't change.

		# Load the resampled file.
		feed = csvfeed.GenericBarFeed(barfeed.Frequency.DAY)
		feed.addBarsFromCSV("spy", resampledFile, marketsession.USEquities.getTimezone())
		feed.loadAll()
	
		self.assertEqual(len(feed["spy"]), 25)
		self.assertEqual(feed["spy"][0].getDateTime(), dt.localize(datetime.datetime(2011, 01, 03, 23, 59, 59), marketsession.USEquities.getTimezone()))
		self.assertEqual(feed["spy"][-1].getDateTime(), dt.localize(datetime.datetime(2011, 02, 01, 23, 59, 59), marketsession.USEquities.getTimezone()))

		self.assertEqual(len(resampledBarDS), len(feed["spy"]))
		self.assertEqual(resampledBarDS[0].getDateTime(), dt.as_utc(datetime.datetime(2011, 01, 03, 23, 59, 59)))
		self.assertEqual(resampledBarDS[-1].getDateTime(), dt.as_utc(datetime.datetime(2011, 02, 01, 23, 59, 59)))

def getTestCases():
	ret = []

	ret.append(ResampleTestCase("testResample"))
	ret.append(ResampleTestCase("testResampleMtGoxMinute"))
	ret.append(ResampleTestCase("testResampleMtGoxHour"))
	ret.append(ResampleTestCase("testResampleMtGoxDay"))
	ret.append(ResampleTestCase("testResampleNinjaTraderHour"))
	ret.append(ResampleTestCase("testResampleNinjaTraderDay"))

	return ret

