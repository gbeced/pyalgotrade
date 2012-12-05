# PyAlgoTrade
# 
# Copyright 2012 Gabriel Martin Becedillas Ruiz
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

import pyalgotrade.barfeed
from pyalgotrade.barfeed import csvfeed
from pyalgotrade import bar
from pyalgotrade.utils import dt

import pytz

import types
import datetime

######################################################################
## NinjaTrader CSV parser
# Each bar must be on its own line and fields must be separated by semicolon (;).
#
# Minute Bars Format:
# yyyyMMdd HHmmss;open price;high price;low price;close price;volume
#
# Daily Bars Format:
# yyyyMMdd;open price;high price;low price;close price;volume
#
# The exported data will be in the UTC time zone.

class Frequency:
	MINUTE = pyalgotrade.barfeed.Frequency.MINUTE
	DAILY = pyalgotrade.barfeed.Frequency.DAY

class RowParser(csvfeed.RowParser):
	def __init__(self, frequency, dailyBarTime, timezone = None):
		self.__frequency = frequency
		self.__dailyBarTime = dailyBarTime
		self.__timezone = timezone

	def __parseDateTime(self, dateTime):
		ret = None
		if self.__frequency == pyalgotrade.barfeed.Frequency.MINUTE:
			ret = datetime.datetime.strptime(dateTime, "%Y%m%d %H%M%S")
		elif self.__frequency == pyalgotrade.barfeed.Frequency.DAY:
			ret = datetime.datetime.strptime(dateTime, "%Y%m%d")
			# Time on CSV files is empty. If told to set one, do it.
			if self.__dailyBarTime != None:
				ret = datetime.datetime.combine(ret, self.__dailyBarTime)
		else:
			assert(False)

		# According to NinjaTrader documentation the exported data will be in UTC.
		ret = pytz.utc.localize(ret)

		# Localize bars if a market session was set.
		if self.__timezone:
			ret = dt.localize(ret, self.__timezone)
		return ret

	def getFieldNames(self):
		return ["Date Time", "Open", "High", "Low", "Close", "Volume"]

	def getDelimiter(self):
		return ";"

	def parseBar(self, csvRowDict):
		dateTime = self.__parseDateTime(csvRowDict["Date Time"])
		close = float(csvRowDict["Close"])
		open_ = float(csvRowDict["Open"])
		high = float(csvRowDict["High"])
		low = float(csvRowDict["Low"])
		volume = float(csvRowDict["Volume"])
		return bar.Bar(dateTime, open_, high, low, close, volume, None)

class Feed(csvfeed.BarFeed):
	"""A :class:`pyalgotrade.barfeed.csvfeed.BarFeed` that loads bars from CSV files exported from NinjaTrader.

	:param frequency: The frequency of the bars.
	:param timezone: The default timezone to use to localize bars. Check :mod:`pyalgotrade.marketsession`.
	:type timezone: A pytz timezone.

	.. note::

		Valid **frequency** parameter values are:

		 * pyalgotrade.barfeed.Frequency.MINUTE 
		 * pyalgotrade.barfeed.Frequency.DAY
	"""

	def __init__(self, frequency, timezone = None):
		if type(timezone) == types.IntType:
			raise Exception("timezone as an int parameter is not supported anymore. Please use a pytz timezone instead.")

		csvfeed.BarFeed.__init__(self, frequency)
		self.__timezone = timezone

	def addBarsFromCSV(self, instrument, path, timezone = None):
		"""Loads bars for a given instrument from a CSV formatted file.
		The instrument gets registered in the bar feed.
		
		:param instrument: Instrument identifier.
		:type instrument: string.
		:param path: The path to the file.
		:type path: string.
		:param timezone: The timezone to use to localize bars. Check :mod:`pyalgotrade.marketsession`.
		:type timezone: A pytz timezone.
		"""

		if type(timezone) == types.IntType:
			raise Exception("timezone as an int parameter is not supported anymore. Please use a pytz timezone instead.")

		if timezone is None:
			timezone = self.__timezone

		rowParser = RowParser(self.getFrequency(), self.getDailyBarTime(), timezone)
		csvfeed.BarFeed.addBarsFromCSV(self, instrument, path, rowParser)

